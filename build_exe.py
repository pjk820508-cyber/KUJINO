"""
build_exe.py - KUJINO를 단일 EXE 파일로 빌드

사용법:
    pip install pyinstaller
    python build_exe.py

결과:
    Windows -> dist/KUJINO.exe
    Mac/Linux -> dist/KUJINO
"""

import os
import sys
import subprocess
import shutil


def main():
    print("=" * 50)
    print("  KUJINO - EXE 빌드 시작")
    print("=" * 50)

    # PyInstaller 확인
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} 감지")
    except ImportError:
        print("✗ PyInstaller가 설치되어 있지 않습니다.")
        print("  설치: pip install pyinstaller")
        sys.exit(1)

    # PyQt5 확인
    try:
        import PyQt5
        print("✓ PyQt5 감지")
    except ImportError:
        print("✗ PyQt5가 설치되어 있지 않습니다.")
        print("  설치: pip install PyQt5")
        sys.exit(1)

    # 이전 빌드 청소
    print("\n이전 빌드 청소 중...")
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  {folder}/ 삭제됨")
    for f in os.listdir("."):
        if f.endswith(".spec"):
            os.remove(f)
            print(f"  {f} 삭제됨")

    # PyInstaller 옵션
    # 플랫폼별로 --add-data 구분자가 다름 (Windows: ; / Mac/Linux: :)
    sep = ";" if sys.platform.startswith("win") else ":"

    args = [
        "pyinstaller",
        "--name=KUJINO",
        "--onefile",      # 단일 EXE
        "--windowed",     # 콘솔 창 숨김
        "--clean",
        f"--add-data=assets{sep}assets",  # 로고 이미지 포함
        "--hidden-import=pygame",  # pygame 의존성 명시
        # "--icon=assets/logo.png",  # 아이콘으로 쓰고 싶다면 주석 해제 (Windows는 .ico 필요)
        "kujino_app.py",
    ]

    print(f"\n빌드 명령:\n  {' '.join(args)}\n")
    print("빌드 진행 중... (1~3분 소요)\n")

    result = subprocess.run(args)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("  ✓ 빌드 성공!")
        print("=" * 50)
        if sys.platform.startswith("win"):
            exe = "dist\\KUJINO.exe"
        else:
            exe = "dist/KUJINO"
        print(f"\n  실행 파일: {exe}")
        print("  더블클릭하여 실행하세요.\n")
        print("  ⚠ 처음 실행 시 같은 폴더에 kujino_data.json과")
        print("    images/ 폴더가 자동으로 만들어집니다.\n")
    else:
        print("\n✗ 빌드 실패. 위 로그를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
