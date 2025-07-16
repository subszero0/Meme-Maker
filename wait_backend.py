import time, requests, sys
url = 'http://localhost:8000/health'
for _ in range(60):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            print('Backend healthy')
            sys.exit(0)
    except Exception:
        pass
    time.sleep(5)
print('Backend not healthy')
sys.exit(1)