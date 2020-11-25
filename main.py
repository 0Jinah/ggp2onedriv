import os

# 파일정리에서 제외될 확장자
exceptExtensions = ['json', 'ini', 'exe']

# 작업할 폴더 경로
workDir = '.\\Takeout\\Google 포토'


# func 전체 대상 파일 계산
def get_total_target_files():
    total_files = 0

    # 폴더 탐색
    for curDir, subDir, files in os.walk(workDir):
        # 파일 확인
        for file in files:
            extension = os.path.splitext(file)[1][1:]  # 현재 파일 확장자
            origin_file_name = os.path.splitext(file)[0]  # 현재 파일명

            if extension not in exceptExtensions and '메타데이터' not in origin_file_name:
                total_files += 1
                # print(f'curDir : {curDir}, origin_file_name : {origin_file_name}, extension : {extension}')

    return total_files


# func 폴더 탐색
def loop_folder(dir_path):
    # 폴더 탐색
    for curDir, subDir, files in os.walk(dir_path):
        # print(f'curDir : {curDir}, subDir : {subDir}')

        # 파일 확인
        for file in files:
            extension = os.path.splitext(file)[1][1:]  # 현재 파일 확장자
            origin_file_name = os.path.splitext(file)[0]  # 현재 파일명

            # print(f'origin_file_name : {origin_file_name}, extension : {extension}')


# 폴더 생성(월단위)

# 파일명 변경

# 파일 생성일, 수정일 변경


if __name__ == '__main__':
    print(f'총 대상 파일 : {get_total_target_files()}')
