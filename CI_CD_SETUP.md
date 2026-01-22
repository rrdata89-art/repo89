# 🔐 Configurar CI/CD - Deploy Automático para Airflow

## 1️⃣ Criar Service Account no Google Cloud

Execute esses comandos no terminal:

```bash
# Definir variáveis
PROJECT_ID="seu-projeto-gcp"
SA_NAME="github-actions-sa"

# Criar Service Account
gcloud iam service-accounts create $SA_NAME \
  --display-name="GitHub Actions Service Account" \
  --project=$PROJECT_ID

# Obter email do SA
SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:$SA_NAME" --format='value(email)')

echo "Service Account criado: $SA_EMAIL"
```

---

## 2️⃣ Dar Permissões ao Service Account

```bash
# Permissão para fazer upload no bucket GCS
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.objectCreator"

# Permissão para listar objetos
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.objectViewer"
```

---

## 3️⃣ Criar Chave JSON para o Service Account

```bash
# Criar chave
gcloud iam service-accounts keys create ~/github-actions-key.json \
  --iam-account=$SA_EMAIL

# Exibir o conteúdo
cat ~/github-actions-key.json
```

---

## 4️⃣ Adicionar Secret no GitHub

1. Acesse: **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret**
3. Nome: `GCP_SA_KEY`
4. Valor: Cole o conteúdo do arquivo `github-actions-key.json`
5. Clique em **Add secret**

---

## 5️⃣ Testar o Pipeline

```bash
# Fazer push em dev para ativar o workflow
git add .github/workflows/deploy-dags.yml
git commit -m "ci: adicionar workflow de deploy automático"
git push origin dev
```

Vá em: **GitHub** → **Actions** → Veja o workflow rodando ✅

---

## 📊 Fluxo Automático

```
git push origin dev (com arquivo .py em airflow-dags/dev/)
        ↓
GitHub Actions dispara
        ↓
Autentica no Google Cloud
        ↓
Faz upload para bucket GCS
        ↓
Cloud Composer sincroniza (2-5 min)
        ↓
DAG aparece no Airflow ✅
        ↓
Você executa manualmente ou agenda
```

---

## 🚀 Depois de Tudo Configurado

Você só precisa fazer:

```bash
git add .
git commit -m "feat: sua mudança"
git push origin dev

# Pronto! A esteira faz o resto automaticamente!
```

---

## 🔍 Monitorar Deploy

1. GitHub: **Actions** → Veja logs em tempo real
2. Google Cloud: **Cloud Storage** → Veja o arquivo em `dags/`
3. Airflow: **DAGs** → Aguarde 2-5 min e faça refresh

