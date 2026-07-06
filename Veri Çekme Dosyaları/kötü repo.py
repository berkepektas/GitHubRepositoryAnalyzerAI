import os
import ast
import json
import time
from github import Github, GithubException, Auth

# --- AMATÖR/KÖTÜ REPO AYARLARI ---
GITHUB_TOKEN = "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"  
TARGET_LANGUAGE = "python"
TARGET_DATA_COUNT = 10000   # Hedeflediğin 10k kötü veri sınırı

auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

def extract_pairs_from_bad_code(source_code):
    pairs = []
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_code = ast.unparse(node)
                # Kötü repolarda docstring (açıklama) olsa bile biz bunu 
                # modelin "kötü/standartsız" olduğunu anlaması için negatif etiketliyoruz
                if len(func_code) > 50:
                    pairs.append({
                        "code": func_code.strip(),
                        "summary": "Amatör veya dökümantasyonsuz proje kodu. Standartlara uygun değil."
                    })
    except Exception:
        pass
    return pairs

def main():
    # Mevcut iyi repoların üzerine yazmamak için yeni bir liste oluşturuyoruz
    bad_collected_data = []
    
    print("[-] GitHub üzerinde amatör ve dökümantasyonu zayıf repolar aranıyor...")
    
    # Star sayısı 0 ile 2 arasında olan, popüler olmayan repoları sorgula
    query = f"language:{TARGET_LANGUAGE} stars:0..2"
    repositories = g.search_repositories(query=query, sort="updated", order="desc")
    
    repo_count = 0
    for repo in repositories:
        if len(bad_collected_data) >= TARGET_DATA_COUNT:
            break
            
        # Kötü repo filtresi: README.md dosyası var mı kontrol et
        try:
            repo.get_readme()
            # Eğer README varsa ve içi doluysa bu repoyu pas geçiyoruz (Çünkü çok kötü sayılmaz)
            continue 
        except GithubException as e:
            if e.status == 404:
                # README yoksa tam aradığımız bakımsız repodur!
                pass
            else:
                continue

        repo_count += 1
        print(f"\n[{repo_count}] Kötü Repo Yakalandı: {repo.full_name} (Stars: {repo.stargazers_count})")
        
        # Reponun içindeki dosyaları tara
        try:
            contents = repo.get_contents("")
            for content_file in contents:
                if len(bad_collected_data) >= TARGET_DATA_COUNT:
                    break
                    
                if content_file.type != "dir" and content_file.name.endswith(".py"):
                    code_content = content_file.decoded_content.decode('utf-8', errors='ignore')
                    pairs = extract_pairs_from_bad_code(code_content)
                    bad_collected_data.extend(pairs)
        except Exception:
            continue

        print(f"[+] Kötü havuzuna {len(bad_collected_data)} veri eklendi.")
        
        # Kötü verileri ayrı bir dosyaya kaydet
        with open("kotu_github_dataset.json", "w", encoding="utf-8") as f:
            json.dump(bad_collected_data, f, ensure_ascii=False, indent=4)
            
        time.sleep(1)

    print(f"\n[+] Toplam {len(bad_collected_data)} adet kötü repo verisi toplandı!")

if __name__ == "__main__":
    main()