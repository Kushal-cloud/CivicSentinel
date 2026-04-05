import requests
with open("test_image.jpg", "wb") as f:
    f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00" + b"\x00"*100)

res = requests.post(
    "http://127.0.0.1:8000/api/complaints/upload",
    files={"image": ("test_image.jpg", open("test_image.jpg", "rb"), "image/jpeg")},
    data={
        "language": "en",
        "tone": "formal"
    }
)
print("Status:", res.status_code)
print("Response:", res.text)
