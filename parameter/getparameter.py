# coding=utf-8
import sys

def main():
    if len(sys.argv) > 1:
        # 获取第一个参数
        first_arg = sys.argv[1]
        print(f"Received argument: {first_arg}")
    else:
        print("No arguments were passed!")

if __name__ == "__main__":
    main()