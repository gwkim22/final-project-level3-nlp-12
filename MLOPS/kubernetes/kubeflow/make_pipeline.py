import pickle

import kfp

from kfp import onprem
from kfp.components import create_component_from_func
from kfp.dsl import ParallelFor, pipeline

def first_stage(cnt: int) -> str:
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("", username="root", port="", key_filename="/var/data/jd_key", password="")

    stdin, stdout, stderr = ssh.exec_command(
        f"cd /opt/ml/final/model && conda activate JD && python stt_sent_test.py --input_file /opt/ml/final/serving/input/video_{cnt}.mp4"
    )
    sentiment_string = stdout.readline().strip()
    stdin.close()
    ssh.close()

    return sentiment_string


def second_stage(sentiment_string: str, ip: str, port: str, key: str, pw: str, conda: str, cnt: int) -> str:
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="root", port=port, key_filename=f"/var/data/{key}_key", password=pw)

    stdin, stdout, stderr = ssh.exec_command(
        f'cd /opt/ml/final/model && conda activate {conda} && python riffusion_pipeline_test.py --sentiment_string "{sentiment_string}" --code {cnt}'
    )
    results = stdout.readlines()
    # print(results)
    stdin.close()
    ssh.close()
    ret = "Compelete"
    return ret


first_stage_op = create_component_from_func(first_stage, packages_to_install=["paramiko==3.0.0"])
second_stage_op = create_component_from_func(second_stage, packages_to_install=["paramiko==3.0.0"])


@pipeline(name="test_pipeline")
def my_pipeline(count: int):
    pvc_name = "kfpvc"
    volume_name = "pipeline"
    volume_mount_path = "var/data"

    with open("server_secret_key.p", "rb") as file:
        gw = pickle.load(file)
        yc = pickle.load(file)
        sol = pickle.load(file)
        dw = pickle.load(file)
    server_secret_key = [gw, yc, sol, dw]

    task_1 = first_stage_op(count).apply(
        onprem.mount_pvc(pvc_name, volume_name=volume_name, volume_mount_path=volume_mount_path)
    )
    with ParallelFor(server_secret_key) as item:
        second_stage_op(task_1.output, item.ip, item.port, item.key, item.pw, item.conda, count).apply(
            onprem.mount_pvc(pvc_name, volume_name=volume_name, volume_mount_path=volume_mount_path)
        )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(my_pipeline, "./02011018_pipeline.yaml")
    print("Compelete")
