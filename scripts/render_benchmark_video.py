"""Render true SMPL surface meshes for a common canonical benchmark walk.

Requires the research runtime, opencv-python, separately acquired SMPL and
local prediction tensors. The renderer uses SMPL forward kinematics and its
original triangle topology. No participant labels or motion tensors are
included in the resulting MP4/GIF.
"""
from pathlib import Path
import argparse
import gc
import json
import os
import subprocess
import sys
import warnings

os.environ.setdefault('KMP_DUPLICATE_LIB_OK','TRUE')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'TransPose'))
import numpy as np
for name,kind in [('bool',bool),('int',int),('float',float),('complex',complex),('object',object),('str',str),('unicode',str)]:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',FutureWarning)
        if not hasattr(np,name):setattr(np,name,kind)
import torch
import articulate as art
import cv2


def load(path):
    try:return torch.load(path,map_location='cpu',weights_only=False,mmap=True)
    except RuntimeError:return torch.load(path,map_location='cpu',weights_only=False)


def centered_text(image,text,x,y,size,color,thickness=1):
    font=cv2.FONT_HERSHEY_SIMPLEX
    width=cv2.getTextSize(text,font,size,thickness)[0][0]
    cv2.putText(image,text,(round(x-width/2),round(y)),font,size,color,thickness,cv2.LINE_AA)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=ROOT)
    parser.add_argument('--index',type=int,default=0)
    parser.add_argument('--seconds',type=float,default=4)
    parser.add_argument('--out',type=Path,default=ROOT/'assets/five-model-comparison.mp4')
    args=parser.parse_args()
    torch.set_num_threads(4)
    model=art.ParametricModel(str(args.project/'Models/smpl_models/smpl/SMPL_NEUTRAL.pkl'))
    names=['GT','TransPose','PIP raw','DynaIP','PNP','TIP']
    # RGB display colors; OpenCV receives BGR.
    colors=np.array([[75,171,244],[60,202,180],[237,173, 70],[151,131,230],[214,139,169],[135,164,195]],dtype=float)
    colors=colors[:,::-1]
    series=[];counts=[];reference_id=None
    source_stride=5
    for name,folder in [('TransPose','TransPose'),('PIP raw','PIP'),('DynaIP','DynaIP'),('PNP','PNP'),('TIP','TIP')]:
        run='CAREPD_BMCLab_raw_batch' if folder=='PIP' else 'CAREPD_BMCLab_batch'
        payload=load(args.project/folder/'data/results'/run/'predictions.pt')
        counts.append(len(payload['pose_pred']))
        assert counts[-1]==counts[0],'Canonical walk counts differ'
        if 'index' in payload:assert int(payload['index'][args.index])==args.index
        if payload.get('manifest'):
            item=payload['manifest'][args.index]
            identity=(item.get('subject_id'),item.get('walk_id'))
            if reference_id is None:reference_id=identity
            if all(identity) and all(reference_id):assert identity==reference_id,'Canonical walk identity differs'
        keys=['pose_gt','pose_pred'] if name=='TransPose' else ['pose_pred']
        for key in keys:
            pose=payload[key][args.index][:round(args.seconds*60):source_stride].detach().cpu().float()
            if pose.shape[-2:]!=(3,3):pose=art.math.axis_angle_to_rotation_matrix(pose.reshape(-1,3)).reshape(-1,24,3,3)
            with torch.no_grad():_,joints,vertices=model.forward_kinematics(pose,calc_mesh=True)
            series.append((vertices-joints[:,:1]).numpy())
        del payload
        gc.collect()
        print('Prepared SMPL mesh:',name,flush=True)
    faces=np.asarray(model.face,dtype=np.int32)
    azimuth=np.deg2rad(-65);elevation=np.deg2rad(10)
    view=np.array([np.cos(azimuth)*np.cos(elevation),np.sin(elevation),np.sin(azimuth)*np.cos(elevation)])
    right=np.array([-np.sin(azimuth),0,np.cos(azimuth)])
    up=np.cross(view,right)
    if up[1]<0:up=-up
    basis=np.stack([right,up,view])
    light=np.array([-.3,.8,.5]);light/=np.linalg.norm(light)
    width,height=1800,720
    centers=np.linspace(150,1650,6)
    scale=245
    frame_count=min(len(v) for v in series)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    command=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}','-r','12','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(args.out)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for frame in range(frame_count):
            image=np.full((height,width,3),(49,28,13),np.uint8)
            cv2.putText(image,'PD GAIT BENCHMARK  /  SMPL MESH RECONSTRUCTION',(55,48),cv2.FONT_HERSHEY_SIMPLEX,.95,(255,255,255),2,cv2.LINE_AA)
            cv2.putText(image,'Six virtual IMUs | one common walk | pelvis-centered | original playback speed',(55,84),cv2.FONT_HERSHEY_SIMPLEX,.55,(222,208,189),1,cv2.LINE_AA)
            centered_text(image,'Qualitative example - column spacing does not represent predicted global translation',width/2,685,.55,(222,208,189))
            for name,color,values,center in zip(names,colors,series,centers):
                centered_text(image,name,center,140,.75,tuple(color),2)
                vertices=values[frame]
                projected=vertices@basis.T
                xy=np.column_stack([center+scale*projected[:,0],390-scale*projected[:,1]])
                triangles=xy[faces].round().astype(np.int32)
                depths=projected[faces,2].mean(axis=1)
                world_triangles=vertices[faces]
                normals=np.cross(world_triangles[:,1]-world_triangles[:,0],world_triangles[:,2]-world_triangles[:,0])
                normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-10)
                # Two-sided directional shading preserves visibility for varied body orientations.
                intensity=.48+.52*np.abs(normals@light)
                face_colors=np.clip(color[None,:]*intensity[:,None],0,255).astype(np.uint8)
                for face in np.argsort(depths):
                    cv2.fillConvexPoly(image,triangles[face],tuple(int(c) for c in face_colors[face]),lineType=cv2.LINE_AA)
            process.stdin.write(image.tobytes())
            if frame%12==0:print('Rendered',frame,'of',frame_count,flush=True)
    finally:
        process.stdin.close()
    if process.wait()!=0:raise RuntimeError('ffmpeg mesh encoding failed')
    args.out.with_suffix('.json').write_text(json.dumps({'source':'MoCap-derived canonical SMPL / virtual six-IMU inputs','renderer':'original SMPL triangle surface meshes, neutral body shape','display':'pelvis-centered, matching canonical walk identity and source frames','qualitative_example':True,'fps':12,'source_fps':60,'frame_stride':source_stride,'frames':frame_count,'models':names},indent=2)+'\n')
    print('Saved SMPL video:',args.out,flush=True)

if __name__=='__main__':main()
