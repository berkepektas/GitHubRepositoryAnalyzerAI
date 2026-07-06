import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np

# Makine Öğrenmesi Kütüphaneleri
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_curve, auc

# Güçlü Modellerimiz
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

# Grafik Entegrasyonu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ModelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yazılım Mühendisliği - Gelişmiş Model Karşılaştırma Laboratuvarı")
        self.root.geometry("1300x800") # Hata veren satır tamamen düzeltildi
        self.root.configure(bg="#F4F7F6") 

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#F4F7F6", foreground="#333333", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#E0E7E9", foreground="#2C3E50")
        self.style.map("TButton", background=[("active", "#BDC3C7")])

        self.X_train, self.X_test, self.y_train, self.y_test = None, None, None, None
        self.vectorizer = TfidfVectorizer(max_features=2500) 

        self.create_widgets()

    def create_widgets(self):
        # --- ÜST PANEL (KONTROL) ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.status_label = ttk.Label(top_frame, text="Durum: Veri bekleniyor... (Train/Test: %80-%20 | Class Weight: Balanced)", font=("Segoe UI", 11, "italic"))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.btn_load = ttk.Button(top_frame, text="1. Verileri Yükle & İşle", command=self.load_and_preprocess)
        self.btn_load.pack(side=tk.RIGHT, padx=5)

        self.btn_train = ttk.Button(top_frame, text="2. 6 Modeli Eğit & Yarıştır", command=self.train_models, state=tk.DISABLED)
        self.btn_train.pack(side=tk.RIGHT, padx=5)

        # --- ORTA PANEL ---
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # SOL PANEL: Sonuç Tablosu
        left_frame = ttk.LabelFrame(main_frame, text=" Model Performans Metrikleri ", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        columns = ("model", "accuracy", "precision", "recall", "f1")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=8)
        self.tree.heading("model", text="Algoritma")
        self.tree.heading("accuracy", text="Accuracy (Doğruluk)")
        self.tree.heading("precision", text="Precision")
        self.tree.heading("recall", text="Recall")
        self.tree.heading("f1", text="F1-Score")
        
        self.tree.column("model", width=180, anchor=tk.CENTER)
        self.tree.column("accuracy", width=110, anchor=tk.CENTER)
        self.tree.column("precision", width=90, anchor=tk.CENTER)
        self.tree.column("recall", width=90, anchor=tk.CENTER)
        self.tree.column("f1", width=90, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.txt_comment = tk.Text(left_frame, height=14, bg="#FFFFFF", fg="#2C3E50", font=("Segoe UI", 10), wrap=tk.WORD, bd=1, relief=tk.SOLID)
        self.txt_comment.pack(fill=tk.X, pady=15)
        self.txt_comment.insert(tk.END, "Analiz Raporu: 6 farklı model yarıştırıldıktan sonra veri dengesizliği optimizasyon sonuçları burada gerekçeleriyle sunulacaktır.")

        # SAĞ PANEL: ROC Eğrisi Grafiği
        self.right_frame = ttk.LabelFrame(main_frame, text=" ROC Eğrisi Grafiği (İyi Repoları Ayırt Etme Gücü) ", padding=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.fig.patch.set_facecolor('#F4F7F6')
        self.ax.set_facecolor('#FFFFFF')
        self.ax.plot([0, 1], [0, 1], 'k--', label="Rastgele Tahmin (0.50)")
        self.ax.set_xlabel('False Positive Rate (FPR)')
        self.ax.set_ylabel('True Positive Rate (TPR)')
        self.ax.legend()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_and_preprocess(self):
        self.status_label.config(text="Durum: JSON dosyaları okunuyor ve harmanlanıyor...")
        self.root.update()

        all_data = []
        files = {
            "devasa_github_dataset.json": 2,  # İyi
            "orta_github_dataset.json": 1,    # Orta
            "kotu_github_dataset.json": 0     # Kötü
        }

        loaded_files_count = 0
        for filename, label in files.items():
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        if "code" in item:
                            all_data.append({"code": item["code"], "label": label})
                loaded_files_count += 1

        if len(all_data) == 0:
            messagebox.showerror("Hata", "Aynı klasörde geçerli JSON veri seti bulunamadı!\nLütfen JSON dosyalarının bu script ile yan yana olduğundan emin olun.")
            return

        df = pd.DataFrame(all_data)

        X = self.vectorizer.fit_transform(df['code'])
        y = df['label'].values

        # %80 Train - %20 Test Bölünmesi
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.status_label.config(text=f"Durum: {len(all_data)} satır veri yüklendi. Bölünme %80/%20 olarak uygulandı.")
        self.btn_train.config(state=tk.NORMAL)
        messagebox.showinfo("Başarılı", f"{loaded_files_count} veri havuzu başarıyla bağlandı!")

    def train_models(self):
        if self.X_train is None:
            return

        self.status_label.config(text="Durum: 6 farklı yapay zeka modeli eğitiliyor, lütfen bekleyin...")
        self.root.update()

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.ax.clear()
        self.ax.plot([0, 1], [0, 1], 'k--', label="Rastgele Tahmin (0.50)")

        # Dengesizlik problemini çözen 'class_weight=balanced' entegrasyonu
        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42),
            "Naive Bayes (Multinomial)": MultinomialNB(),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=12, class_weight="balanced", n_jobs=-1, random_state=42),
            "Linear SVM (Olasılık Ayarlı)": CalibratedClassifierCV(LinearSVC(class_weight="balanced", dual=False, random_state=42)),
            "SGD Classifier (Optimize)": SGDClassifier(loss="log_loss", class_weight="balanced", random_state=42),
            "HistGradient Boosting": HistGradientBoostingClassifier(max_depth=6, random_state=42)
        }

        best_model_name = ""
        best_f1 = 0
        report_text = "=== ADALETLİ MODEL ANALİZİ VE DEĞERLENDİRME RAPORU ===\n\n"
        report_text += "[BİLGİ]: Eğitimde sınıf dengesizliğini çözmek için 'class_weight=balanced' kullanılmıştır.\n\n"

        for name, model in models.items():
            if name == "HistGradient Boosting":
                model.fit(self.X_train.toarray(), self.y_train)
                y_pred = model.predict(self.X_test.toarray())
                y_proba = model.predict_proba(self.X_test.toarray())
            else:
                model.fit(self.X_train, self.y_train)
                y_pred = model.predict(self.X_test)
                y_proba = model.predict_proba(self.X_test)

            acc = accuracy_score(self.y_test, y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(self.y_test, y_pred, average='macro', zero_division=0)

            self.tree.insert("", tk.END, values=(name, f"{acc:.4f}", f"{prec:.4f}", f"{rec:.4f}", f"{f1:.4f}"))

            if f1 > best_f1:
                best_f1 = f1
                best_model_name = name

            fpr, tpr, _ = roc_curve(self.y_test == 2, y_proba[:, 2])
            roc_auc = auc(fpr, tpr)
            self.ax.plot(fpr, tpr, label=f'{name} (AUC = {roc_auc:.2f})')

            report_text += f"• {name} -> F1-Score (Dengeli Başarı): {f1*100:.2f}%\n"

        self.ax.set_xlabel('False Positive Rate (FPR)')
        self.ax.set_ylabel('True Positive Rate (TPR)')
        self.ax.set_title('Modellerin Kalite Ayırt Etme Gücü (ROC/AUC)')
        self.ax.legend(loc="lower right")
        self.canvas.draw()

        report_text += f"\n[MÜHENDİSLİK KARARI]: Sınıf dengesizliği ortadan kaldırıldığında en yüksek kararlılığı gösteren şampiyon model: '{best_model_name}'."
        report_text += "\nBu model, kötü yazılmış amatör kodlar ile ortalama projeleri birbirine karıştırmadan ayırt etme yeteneğine sahip."

        self.txt_comment.delete(1.0, tk.END)
        self.txt_comment.insert(tk.END, report_text)
        self.status_label.config(text="Durum: 6 Model adil şartlarda yarıştırıldı. Sonuçlar hazır.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModelApp(root)
    root.mainloop()