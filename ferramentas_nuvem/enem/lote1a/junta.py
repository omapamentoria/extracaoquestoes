import cv2,sys,numpy as np
ims=[cv2.imread(f) for f in sys.argv[2:]]; w=max(i.shape[1] for i in ims)
out=np.vstack([cv2.copyMakeBorder(i,0,8,0,w-i.shape[1],cv2.BORDER_CONSTANT,value=(0,0,255)) for i in ims]); cv2.imwrite(sys.argv[1],out)
