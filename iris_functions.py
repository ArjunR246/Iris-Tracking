import numpy as np

def euclid(a, b):
    return np.linalg.norm(a - b)

def EAR(pts):
    # pts: array of 6 (x,y) points for the eye
    A = euclid(pts[1], pts[5])
    B = euclid(pts[2], pts[4])
    C = euclid(pts[0], pts[3])
    return (A + B) / (2.0 * C)

def iris_center(pts):
    return np.mean(pts, axis=0)

def iris_circularity(pts):
    center = np.mean(pts, axis=0)
    dist = np.linalg.norm(pts - center, axis=1)
    return np.std(dist) / (np.mean(dist) + 1e-8)
