import os
import ast
import json
import time
import socket
from github import Github, GithubException, Auth

# --- AYARLAR ---
GITHUB_TOKEN = "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"  
TARGET_LANGUAGE = "python"  
MIN_STARS = 500             
TARGET_DATA_COUNT = 30000   

# Bağlantıların kilitlenmesini önlemek için zaman aşımı süresi (saniye)
socket.setdefaulttimeout(15)

auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

def extract_pairs_from_code(source_code):
    pairs = []
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_code = ast.unparse(node)
                docstring = ast.get_docstring(node)
                
                if docstring and len(docstring.strip()) > 10 and len(func_code) > 50:
                    pairs.append({
                        "code": func_code.replace(f'"""{docstring}"""', "").strip(),
                        "summary": docstring.strip()
                    })
    except Exception:
        pass
    return pairs

def process_repo_files(repo, path="", current_depth=0, max_depth=4):
    """
    max_depth: Çok derin klasör yapılarına (test klasörleri, virtualenv vs.) 
    girip kodun boğulmasını engeller.
    """
    if current_depth > max_depth:
        return []
        
    pairs = []
    try:
        contents = repo.get_contents(path)
        for content_file in contents:
            if content_file.type == "dir":
                # Sadece ana kaynak kod klasörlerine odaklanmak için test, venv gibi klasörleri ele
                if any(x in content_file.path.lower() for x in ["test", "venv", "env", "node_modules", ".github"]):
                    continue
                time.sleep(0.1) 
                pairs.extend(process_repo_files(repo, content_file.path, current_depth + 1, max_depth))
            elif content_file.name.endswith(".py"):
                try:
                    code_content = content_file.decoded_content.decode('utf-8', errors='ignore')
                    file_pairs = extract_pairs_from_code(code_content)
                    pairs.extend(file_pairs)
                    if file_pairs:
                        print(f"   -> {content_file.name} dosyasından {len(file_pairs)} fonksiyon alındı.")
                except Exception:
                    continue
    except (GithubException, socket.timeout) as e:
        # Zaman aşımı veya kota sınırında bekle ve devam et
        print(f"   [!] Klasör okunurken duraksama yaşandı, atlanıyor veya bekleniyor... (Yol: {path})")
        time.sleep(5)
    return pairs

def main():
    try:
        user_login = g.get_user().login
        print(f"[-] GitHub Bağlantısı Başarılı! Kullanıcı: {user_login}")
    except Exception:
        print("[!] HATA: Token geçersiz veya internet bağlantısı yok!")
        return

    # Mevcut toplanmış veriyi korumak için kontrol et
    all_collected_data = []
    if os.path.exists("devasa_github_dataset.json"):
        try:
            with open("devasa_github_dataset.json", "r", encoding="utf-8") as f:
                all_collected_data = json.load(f)
            print(f"[-] Mevcut veri seti bulundu. Kaldığı yerden devam ediyor. Mevcut Veri: {len(all_collected_data)}")
        except Exception:
            pass

    print(f"[-] Popüler {TARGET_LANGUAGE} repoları taranıyor...")
    
    try:
        repositories = g.search_repositories(query=f"language:{TARGET_LANGUAGE} stars:>{MIN_STARS}", sort="stars", order="desc")
        
        repo_count = 0
        for repo in repositories:
            if len(all_collected_data) >= TARGET_DATA_COUNT:
                break
                
            repo_count += 1
            print(f"\n[{repo_count}] İnceleme Başladı: {repo.full_name} (Stars: {repo.stargazers_count})")
            
            # Repo bazlı zaman aşımı kontrolü ekliyoruz
            start_time = time.time()
            repo_pairs = []
            
            try:
                # Klasör tarama derinliğini 4 ile sınırladık ki takılmasın
                repo_pairs = process_repo_files(repo, max_depth=4)
                all_collected_data.extend(repo_pairs)
            except Exception as e:
                print(f" [!] Repo işlenirken hata oluştu, sonraki repoya geçiliyor: {e}")
                continue
                
            print(f"[+] Bu repodan {len(repo_pairs)} çift alındı. Toplam Veri: {len(all_collected_data)} / {TARGET_DATA_COUNT}")
            
            # Anlık disk kaydı
            with open("devasa_github_dataset.json", "w", encoding="utf-8") as f:
                json.dump(all_collected_data, f, ensure_ascii=False, indent=4)
                
            # Bir repoya maksimum 3 dakika sınır koy (Takılmayı tamamen önler)
            if time.time() - start_time > 180:
                print(" [!] Bu repo çok uzun sürdü, süre sınırından dolayı sonraki repoya geçiliyor.")
                
            time.sleep(2)

    except GithubException as e:
        print(f"[!] Genel GitHub API hatası: {e}")

    print(f"\n[+] İşlem tamamlandı! Toplam Veri: {len(all_collected_data)}")

if __name__ == "__main__":
    main()