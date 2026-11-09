import socket

def test_connection(host, port, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    print(f"正在测试连接 {host}:{port} ...", end=" ")
    try:
        s.connect((host, port))
        s.close()
        print(" 通畅 (成功连接)")
        return True
    except socket.timeout:
        print(" 连接超时 (被网络/防火墙/代理阻断)")
    except Exception as e:
        print(f" 失败 ({e})")
    return False

if __name__ == '__main__':
    host = "smtp.qq.com"
    print("------ 开始检测 QQ 邮箱 SMTP 端口 ------")
    test_connection(host, 465)
    test_connection(host, 587)