"""Render a common-walk, pelvis-centered comparison from local model outputs.

Requires the research runtime, separately obtained SMPL, and ffmpeg on PATH.
No tensors or participant labels are copied into the output assets.
"""
from pathlib import Path
import argparse
import gc
import json
import os
import sys

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'TransPose'))
import numpy as np
import warnings
for name,kind in [('bool',bool),('int',int),('float',float),('complex',complex),('object',object),('str',str),('unicode',str)]:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',FutureWarning)
        if not hasattr(np,name):setattr(np,name,kind)
import torch
import articulate as art
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

def load(path):
    try:return torch.load(path,map_location='cpu',weights_only=False,mmap=True)
    except RuntimeError:return torch.load(path,map_location='cpu',weights_only=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=ROOT)
    parser.add_argument('--index',type=int,default=0)
    parser.add_argument('--seconds',type=float,default=4)
    parser.add_argument('--out',type=Path,default=ROOT/'assets/five-model-comparison.mp4')
    args=parser.parse_args()
    model=art.ParametricModel(str(args.project/'Models/smpl_models/smpl/SMPL_NEUTRAL.pkl'))
    names=['GT','TransPose','PIP raw','DynaIP','PNP','TIP']
    colors=['#62b7ff','#5dd7c1','#e9b456','#aa9cff','#e29cb8','#9db7d0']
    positions=[]
    source_count=None
    for name,folder in [('TransPose','TransPose'),('PIP raw','PIP'),('DynaIP','DynaIP'),('PNP','PNP'),('TIP','TIP')]:
        run='CAREPD_BMCLab_raw_batch' if folder=='PIP' else 'CAREPD_BMCLab_batch'
        payload=load(args.project/folder/'data/results'/run/'predictions.pt')
        n=len(payload['pose_pred'])
        if source_count is None:source_count=n
        assert n==source_count, 'Model outputs must have the same canonical walk count'
        if 'index' in payload:
            assert int(payload['index'][args.index])==args.index,'Canonical prediction ordering differs'
        keys=['pose_gt','pose_pred'] if name=='TransPose' else ['pose_pred']
        for key in keys:
            pose=payload[key][args.index][:round(args.seconds*60)].detach().cpu().float()
            if pose.shape[-2:]!=(3,3):pose=art.math.axis_angle_to_rotation_matrix(pose.reshape(-1,3)).reshape(-1,24,3,3)
            with torch.no_grad():_,joints=model.forward_kinematics(pose,calc_mesh=False)
            positions.append((joints-joints[:,:1]).numpy())
        del payload
        gc.collect()
        print('Prepared',name,flush=True)
    length=min(len(p) for p in positions)
    # A 60 Hz source sampled every third frame, played at 20 fps.
    frames=list(range(0,length,3))
    fig=plt.figure(figsize=(15,4.7),facecolor='#0d1c31')
    fig.text(.04,.945,'PD GAIT  /  FIVE-MODEL RECONSTRUCTION',color='white',fontsize=18,weight='bold')
    fig.text(.04,.889,'Six virtual IMUs · one common walk · pelvis-centered motion · original playback speed',color='#bdd0e2',fontsize=11)
    fig.text(.5,.035,'Qualitative example — displayed spacing does not represent predicted global translation',color='#bdd0e2',ha='center',fontsize=10)
    parent=model.parent
    artists=[]
    for i,(name,color) in enumerate(zip(names,colors)):
        ax=fig.add_axes([.015+i*.163,.12,.16,.68],projection='3d',facecolor='#0d1c31')
        ax.set_xlim(-.65,.65);ax.set_ylim(-.65,.65);ax.set_zlim(-1.05,1.05)
        ax.set_box_aspect((1,1,1.8));ax.view_init(elev=13,azim=-60)
        ax.set_axis_off();ax.set_title(name,color=color,pad=-5,fontsize=13,weight='bold')
        lines=[]
        for joint in range(1,24):
            line,=ax.plot([],[],[],color=color,lw=2.4)
            lines.append((line,joint,parent[joint]))
        artists.append(lines)
    def update(frame):
        for joints,lines in zip(positions,artists):
            p=joints[frame]
            for line,child,par in lines:
                segment=p[[par,child]]
                line.set_data(segment[:,0],segment[:,2]);line.set_3d_properties(segment[:,1])
        return [line for lines in artists for line,_,_ in lines]
    animation=FuncAnimation(fig,update,frames=frames,interval=50,blit=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    animation.save(str(args.out),writer=FFMpegWriter(fps=20,codec='libx264',extra_args=['-pix_fmt','yuv420p','-movflags','+faststart']),dpi=100)
    plt.close(fig)
    (args.out.with_suffix('.json')).write_text(json.dumps({'source':'MoCap-derived canonical SMPL / virtual six-IMU inputs','display':'pelvis-centered, common canonical sequence and frame indices','qualitative_example':True,'fps':20,'source_fps':60,'frame_stride':3,'frames':len(frames),'models':names},indent=2)+'\n')
    print('Saved',args.out,flush=True)

if __name__=='__main__':main()
