import json
import os
import shutil
import subprocess

# 파일정리에서 제외될 확장자
import jellyfish

exceptExtensions = ['json', 'ini', 'exe']

# 작업할 폴더 경로
workDir = '.\\Takeout\\Google 포토'
excludeDir = '.\\Takeout\\excludeFiles'
resultDir = '.\\Takeout\\resultFiles'

totalTargetFiles = 0


# Print iterations progress
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


# func 전체 대상 파일 계산
def get_total_target_files():
    # 폴더 탐색
    for curDir, subDir, files in os.walk(workDir):
        # 파일 확인
        for file in files:
            extension = os.path.splitext(file)[1][1:]  # 현재 파일 확장자
            origin_file_name = os.path.splitext(file)[0]  # 현재 파일명

            if extension not in exceptExtensions and '메타데이터' not in origin_file_name:
                global totalTargetFiles
                totalTargetFiles += 1


# func 폴더 탐색
def loop_folder():
    progress = 0
    # 폴더 탐색
    for curDir, subDir, files in os.walk(workDir):
        # print(f'curDir : {curDir}, subDir : {subDir}')

        # 파일 확인
        for file in files:
            extension = os.path.splitext(file)[1][1:]  # 현재 파일 확장자
            origin_file_name = os.path.splitext(file)[0]  # 현재 파일명

            if extension not in exceptExtensions and '메타데이터' not in origin_file_name:
                progress += 1
                printProgressBar(progress, totalTargetFiles, 'progress', 'finish', 1, 50, '█', '')

                get_taken_time(curDir, origin_file_name, extension, files)


# 폴더 생성(월단위)

# 파일명 변경

# 파일 생성일, 수정일 변경

# 사진 촬영일 확인
def get_taken_time(cur_dir, origin_file_name, extension, files):
    origin_file_full_path = os.path.join(cur_dir, origin_file_name + '.' + extension)
    origin_meta_file_full_path = origin_file_full_path + '.' + 'json'

    # 메타파일이 있는지 확인
    if os.path.exists(origin_meta_file_full_path):
        # 메타파일이 있는 경우 photoTakenTime 으로 설정
        with open(origin_meta_file_full_path, 'rb') as meta_file:
            meta_data = json.loads(meta_file.read().decode("utf-8"))

            photo_taken_time = meta_data["photoTakenTime"]
            time_stamp = photo_taken_time["timestamp"]
            # print(f'time_stamp : {datetime.datetime.fromtimestamp(int(time_stamp))}')

    else:
        # 메타파일이 없는 경우 비슷한 파일이 있는지 확인
        similar_file, similarity = find_similar_file(origin_file_name, files)

        if len(similar_file) > 0:
            b = 1
            # print(f'origin_file_name : {origin_file_name}, similar_file : {similar_file}, similarity : {similarity}')
        else:
            shutil.copyfile(origin_file_full_path, os.path.join(excludeDir, origin_file_name + '.' + extension))


# 가장 비슷한 파일명 찾기
def find_similar_file(origin_file_name, files):
    similar_file = ''
    similarity = 0

    for file in files:
        cur_file_name = os.path.splitext(file)[0]
        cur_extension = os.path.splitext(file)[1][1:]

        if 'json' == cur_extension:
            cur_similarity = jellyfish.jaro_similarity(origin_file_name, cur_file_name) * 100
            if cur_similarity >= 90 and cur_similarity >= similarity:
                similarity = cur_similarity
                similar_file = cur_file_name

    return similar_file, similarity


def init_process():
    if os.path.exists(excludeDir):
        shutil.rmtree(excludeDir)

    if os.path.exists(resultDir):
        shutil.rmtree(resultDir)

    subprocess.call('mkdir ' + excludeDir, shell=True)
    subprocess.call('mkdir ' + resultDir, shell=True)


if __name__ == '__main__':
    init_process()

    get_total_target_files()  # 총 대상 파일(사진, 동영상 파일만)
    print(f'총 대상 파일 : {totalTargetFiles}')

    # 분류작업 시작
    loop_folder()
