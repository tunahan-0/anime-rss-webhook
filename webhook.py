import requests

def embed_gonder(ad, bolum, link, resim, webhook_url, rol_id): 
    etiket = f"<@&{rol_id}>"
    bolum_fix = bolum.replace("Bolum","Bölüm")
    embed = {
        "title": "Yeni Bölüm",
        "description": f"[**İzlemek için tıkla**]({link})",
        "color": 0xF54927, 
        "image":{
            "url": resim
        },
        "fields": [
            {"name": "Anime", "value": ad, "inline": True},
            {"name": "Bölüm", "value": bolum_fix, "inline": False}
        ]
    }
    
    payload = {
        "content": etiket,
        "embeds": [embed]
    }
    
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code == 204:
        print("Başarılı")
    else:
        print(f"Hata:{response.status_code}")
        print(response.text)
