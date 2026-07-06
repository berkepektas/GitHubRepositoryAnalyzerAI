import os
import ast
import json
import time
import socket
import base64
from github import Github, GithubException, Auth

# --- AYARLAR ---
GITHUB_TOKEN = "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"  
TARGET_LANGUAGE = "python"  
TARGET_DATA_COUNT = 20000       
MAX_PAIRS_PER_REPO = 500        

# Global network zaman aşımı süresi
socket.setdefaulttimeout(5)

auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

def extract_pairs_from_code(source_code, repo_name, repo_stars):
    pairs = []
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_code = ast.unparse(node)
                docstring = ast.get_docstring(node)
                
                if docstring and len(docstring.strip()) > 10 and len(func_code) > 50:
                    pairs.append({
                        "repo_name": repo_name,
                        "repo_stars": repo_stars,
                        "repo_type": "orta_olcek",
                        "code": func_code.replace(f'"""{docstring}"""', "").strip(),
                        "summary": docstring.strip()
                    })
    except Exception:
        pass
    return pairs

def main():
    try:
        print(f"[-] GitHub Bağlantısı Başarılı! Kullanıcı: {g.get_user().login}")
    except Exception:
        print("[!] HATA: Token geçersiz!")
        return

    orta_collected_data = []
    
    if os.path.exists("orta_github_dataset.json"):
        try:
            with open("orta_github_dataset.json", "r", encoding="utf-8") as f:
                orta_collected_data = json.load(f)
            print(f"[-] Mevcut veri seti yüklendi. Kaldığı Yerden Devam Ediyor. Mevcut Veri: {len(orta_collected_data)}")
        except Exception:
            pass

    print(f"[-] Sabırlı ve kota kontrollü orta ölçekli repolar taranıyor...")
    
    query = f"language:{TARGET_LANGUAGE} stars:20..150 forks:5..30"
    repositories = g.search_repositories(query=query, sort="updated", order="desc")
    
    repo_count = 0
    for repo in repositories:
        if len(orta_collected_data) >= TARGET_DATA_COUNT:
            break
            
        repo_count += 1
        print(f"\n[{repo_count}] Tarama Başladı: {repo.full_name} | ⭐ Yıldız Sayısı: {repo.stargazers_count}")
        
        repo_start_time = time.time()
        repo_pairs = []
        
        try:
            sha = repo.get_commits()[0].sha
            tree = repo.get_git_tree(sha, recursive=True).tree
            
            py_files = [
                item for item in tree 
                if item.path.endswith('.py') and not any(x in item.path.lower() for x in ["test", "venv", "env", "node_modules", ".github", "site-packages"])
            ]
            
            print(f"   -> Repoda taranacak {len(py_files)} adet filtrelenmiş Python dosyası bulundu.")
            
            for file_item in py_files:
                # SÜRE SINIRINI 150 SANİYEYE (2.5 DAKİKA) ÇIKARDIK
                if time.time() - repo_start_time > 150:
                    print("   [!] Repo zaman sınırını (2.5 dk) astı, sonraki repoya atlanıyor...")
                    break
                    
                if len(repo_pairs) >= MAX_PAIRS_PER_REPO:
                    break
                    
                try:
                    blob = repo.get_git_blob(file_item.sha)
                    code_content = blob.content
                    code_text = base64.b64decode(code_content).decode('utf-8', errors='ignore')
                    
                    file_pairs = extract_pairs_from_code(code_text, repo.full_name, repo.stargazers_count)
                    repo_pairs.extend(file_pairs)
                    
                except (GithubException, socket.timeout):
                    continue
                    
        except Exception as e:
            print(f" [!] Repo ağacı alınırken hata oluştu, geçiliyor: {e}")
            continue
            
        repo_pairs = repo_pairs[:MAX_PAIRS_PER_REPO]
        if repo_pairs:
            orta_collected_data.extend(repo_pairs)
            print(f"[+] Repodan {len(repo_pairs)} fonksiyon alındı.")
            print(f"[-] Toplam Gelişme: {len(orta_collected_data)} / {TARGET_DATA_COUNT}")
            
            with open("orta_github_dataset.json", "w", encoding="utf-8") as f:
                json.dump(orta_collected_data, f, ensure_ascii=False, indent=4)
        else:
            print(" [~] Bu repodan anlamlı fonksiyon ayıklanamadı.")
            
        time.sleep(1)

    print(f"\n[+] İşlem tamamlandı! Toplam Dengeli Orta Ölçek Verisi: {len(orta_collected_data)}")

if __name__ == "__main__":
    main()