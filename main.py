import datetime
import json
import os
import shutil
import subprocess
import time

import jellyfish

# 파일정리에서 제외될 확장자
exceptExtensions = ['json', 'ini', 'exe']

# 작업할 폴더 경로
workDir = '.\\Takeout\\Google 포토'
excludeDir = '.\\Takeout\\excludeFiles'
resultDir = '.\\Takeout\\resultFiles'

# 작업할 파일 수
totalTargetFiles = 0


# Print iterations progress
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
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
    print('\nconvert start')

    progress = 0
    # 폴더 탐색
    for curDir, subDir, files in os.walk(workDir):

        # 파일 확인
        for file in files:
            extension = os.path.splitext(file)[1][1:]  # 현재 파일 확장자
            origin_file_name = os.path.splitext(file)[0]  # 현재 파일명

            if extension not in exceptExtensions and '메타데이터' not in origin_file_name:
                progress += 1

                # 촬영 시간
                taken_timestamp = int(get_taken_time(curDir, origin_file_name, extension, files))
                taken_time = datetime.datetime.fromtimestamp(taken_timestamp)

                # 복사될 폴더가 없는 경우 폴더 생성
                taken_year = taken_time.year.__str__()
                taken_month = taken_time.month.__str__().zfill(2)
                taken_day = taken_time.day.__str__().zfill(2)

                copy_dir = os.path.join(resultDir, taken_year, taken_month)

                if not os.path.exists(copy_dir):
                    subprocess.call('mkdir ' + copy_dir, shell=True)

                # 변경될 파일명
                rename_file = get_rename_file(copy_dir, origin_file_name, extension, taken_year, taken_month, taken_day)
                # print(f'rename_file = {rename_file}')
                # print(f'orgin_file_name : {origin_file_name}, taken_time : {taken_time}')

                # 파일 복사
                copy_result_folder(curDir, origin_file_name, extension, copy_dir, rename_file)

                set_copy_file_timestamp(copy_dir, rename_file, taken_time)

                # 프로그래스바 출력
                print_progress_bar(progress, totalTargetFiles, 'progress', 'finish', 1, 50, '█', '')


# 복사된 파일 생성일시, 수정일시 변경
def set_copy_file_timestamp(copy_dir, rename_file, taken_time):
    powershell_path = "C:\\windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"
    base_command = f'\"(Get-Item \\\"{os.getcwd()}{copy_dir.replace(".", "")}\\{rename_file}\\\")'
    creation_command = f'.CreationTime=(\\\"{taken_time}\\\")\"'
    modified_command = f'.LastWritetime=(\\\"{taken_time}\\\")\"'
    # print(powershell_path + ' ' + base_command + creation_command)
    subprocess.call(powershell_path + ' ' + base_command + creation_command)
    subprocess.call(powershell_path + ' ' + base_command + modified_command)

    # print(base_command+creation_command)


# 결과 폴더로 파일 복사
def copy_result_folder(cur_dir, origin_file_name, extension, copy_dir, rename_file):
    shutil.copyfile(os.path.join(cur_dir, origin_file_name + '.' + extension), os.path.join(copy_dir, rename_file))

    # 파일이 생성될때까지 대기
    while 1:
        if os.path.exists(os.path.join(copy_dir, rename_file)):
            break
        else:
            time.sleep(1)


# 파일명 변경
def get_rename_file(copy_dir, origin_file_name, extension, taken_year, taken_month, taken_day):
    result_rename_file = ''
    # 중복되지 않는 파일명 확인
    idx = 0
    while 1:
        init_rename_file = taken_year + taken_month + taken_day + '_' + origin_file_name

        if idx != 0:
            init_rename_file += '_' + str(idx)

        if not os.path.exists(os.path.join(copy_dir, init_rename_file + '.' + extension)):

            result_rename_file = init_rename_file
            break
        else:
            idx += 1
            # print(f'init_rename_file : {init_rename_file}')

    return result_rename_file + '.' + extension


# 메타파일 검색
def find_meta_file(cur_dir, origin_file_name, extension, files):
    origin_file_full_path = os.path.join(cur_dir, origin_file_name + '.' + extension)
    origin_meta_file_full_path = origin_file_full_path + '.' + 'json'

    meta_file_name = ''

    # 메타파일이 있는지 확인
    if os.path.exists(origin_meta_file_full_path):
        # 메타파일이 있는 경우 파일명 반환
        meta_file_name = origin_file_name + '.' + extension + '.' + 'json'
        # print(f'1.meta_file_name : {meta_file_name}')

    else:
        # 메타파일이 없는 경우 비슷한 파일이 있는지 확인
        similar_file, similarity = find_similar_file(origin_file_name, files)
        if len(similar_file) > 0:
            meta_file_name = similar_file
            # print(f'2. origin_file_name : {origin_file_name}, meta_file_name : {meta_file_name}')

    return meta_file_name


# 가장 비슷한 파일명 찾기
def find_similar_file(origin_file_name, files):
    similar_file = ''
    similarity = 0

    for file in files:
        cur_file_name = os.path.splitext(file)[0]
        cur_extension = os.path.splitext(file)[1][1:]

        if 'json' == cur_extension:
            cur_similarity = jellyfish.jaro_similarity(origin_file_name, cur_file_name) * 100
            if cur_similarity >= 70 and cur_similarity >= similarity:
                similarity = cur_similarity
                similar_file = cur_file_name + '.' + cur_extension

    return similar_file, similarity


# 사진 촬영일 확인
def get_taken_time(cur_dir, origin_file_name, extension, files):
    origin_file_full_path = os.path.join(cur_dir, origin_file_name + '.' + extension)
    meta_file_name = find_meta_file(cur_dir, origin_file_name, extension, files)

    time_stamp = 0

    if not meta_file_name == '':
        # 메타파일이 있는경우 photoTakenTime에서 timestamp 확인
        with open(os.path.join(cur_dir, meta_file_name), 'rb') as meta_file:
            meta_data = json.loads(meta_file.read().decode("utf-8"))
            photo_taken_time = meta_data["photoTakenTime"]
            time_stamp = photo_taken_time["timestamp"]
            # print(f'time_stamp : {datetime.datetime.fromtimestamp(int(time_stamp))}')
    else:
        # 메타파일이 없는 경우 excludeDir 로 복사
        shutil.copyfile(origin_file_full_path, os.path.join(excludeDir, origin_file_name + '.' + extension))

    return time_stamp


# 초기화
def init_process():
    print('init_process')

    if os.path.exists(excludeDir):
        print(f'delete excludeDir({excludeDir})')
        shutil.rmtree(excludeDir)

    if os.path.exists(resultDir):
        print(f'delete resultDir({resultDir})')
        shutil.rmtree(resultDir)

    print(f'make excludeDir({excludeDir})')
    subprocess.call('mkdir ' + excludeDir, shell=True)

    print(f'make resultDir({resultDir})')
    subprocess.call('mkdir ' + resultDir, shell=True)


def print_banner():
    with open(".\\banner.txt", 'rb') as banner:
        text = banner.read().decode("utf-8")
        print(text)
    banner.close()


if __name__ == '__main__':
    print_banner()

    init_process()

    get_total_target_files()  # 총 대상 파일(사진, 동영상 파일만)
    print(f'\nTotal target files : {totalTargetFiles}')

    # 분류작업 시작
    loop_folder()
