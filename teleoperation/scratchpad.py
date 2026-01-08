import scipy.spatial.transform as transform

rot1 = transform.Rotation.from_quat([-0.5, 0.5, -0.5, 0.5], scalar_first=True)
rot2 = transform.Rotation.from_quat([0, 0.7071, 0.7071, 0], scalar_first=True)

rot12 = rot2 * rot1.inv()

print(rot12.as_quat(scalar_first=True))