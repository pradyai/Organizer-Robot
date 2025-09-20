from urdf2mjcf import run
run(
    urdf_path="./so100.urdf",
    mjcf_path="./so100_mjcf/so100.xml",
    copy_meshes=True,
)
print("Conversion complete!")