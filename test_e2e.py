import urllib.request
import json
import io
from PIL import Image

# 1. Login
login_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login',
    data=json.dumps({'email': 'samirrahane367@gmail.com', 'password': 'samirrahane@2006'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(login_req) as resp:
    token = json.loads(resp.read())['access_token']
print('✅ 1. Login Success! Token:', token[:25] + '...')

# 2. Create sample image
img = Image.new('RGB', (224, 224), color=(34, 139, 34))
buf = io.BytesIO()
img.save(buf, format='JPEG')
img_bytes = buf.getvalue()

# 3. Multipart predict
boundary = '----WebKitFormBoundaryE2ETest123'
body = bytearray()
body.extend(f'--{boundary}\r\n'.encode('utf-8'))
body.extend(b'Content-Disposition: form-data; name="file"; filename="sugarcane_sample.jpg"\r\n')
body.extend(b'Content-Type: image/jpeg\r\n\r\n')
body.extend(img_bytes)
body.extend(b'\r\n')
body.extend(f'--{boundary}\r\n'.encode('utf-8'))
body.extend(b'Content-Disposition: form-data; name="language"\r\n\r\n')
body.extend(b'mr\r\n')
body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

pred_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/predict',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
)

with urllib.request.urlopen(pred_req) as resp:
    result = json.loads(resp.read())
    print('✅ 2. Predict API Success!')
    print('   Scan ID:', result['scan_id'])
    print('   Diagnosed Label:', result['prediction']['label'])
    print('   Confidence:', result['prediction']['confidence'])

# 4. Check history for Samir Rahane
hist_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/history',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(hist_req) as resp:
    hist = json.loads(resp.read())
    print('✅ 3. History API Success!')
    print('   Total scans found for samirrahane367@gmail.com:', hist['total'])
    print('   Returned items length:', len(hist['items']))

# 5. Verify User Isolation: Login as another user and check history
try:
    reg_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/auth/signup',
        data=json.dumps({
            'full_name': 'Second Farmer',
            'email': 'second_farmer@example.com',
            'password': 'password123',
            'phone': '9123456789',
            'language': 'mr'
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(reg_req)
except Exception:
    pass

login_req2 = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login',
    data=json.dumps({'email': 'second_farmer@example.com', 'password': 'password123'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(login_req2) as resp:
    token2 = json.loads(resp.read())['access_token']

hist_req2 = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/history',
    headers={'Authorization': f'Bearer {token2}'}
)
with urllib.request.urlopen(hist_req2) as resp:
    hist2 = json.loads(resp.read())
    print('✅ 4. User Isolation Verified!')
    print('   Total scans for second user (second_farmer@example.com):', hist2['total'])
    assert hist2['total'] == 0, 'Error: Second user should have 0 scans!'
    print('   🎉 Verified: Second user cannot see first user\'s scans!')
