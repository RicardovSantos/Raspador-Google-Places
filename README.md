# 📍 Raspador Google Places

Pesquise negócios no Google Maps (ex.: *salão de beleza na Penha*) e exporte os dados
em **CSV** (planilha) ou **JSON** prontos para importar no seu app de prospecção.

**Campos exportados:** `name`, `phone`, `category`, `city`, `county` (bairro), `website`.

Funciona com a **Places API (New)** do Google — o padrão atual e atualizado.

---

## 📁 Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | App visual (abre no navegador, celular ou PC). **Recomendado.** |
| `raspador_places.py` | Versão por linha de comando (Python). |
| `README.md` | Este guia. |

---

## 🔑 Onde colar a sua chave da API

**No app (index.html):** abra o arquivo no navegador e cole a chave no campo
**🔑 Sua chave da API do Google Places**. Ela fica salva só no seu navegador.

**No Python (raspador_places.py):** use uma destas opções:
1. Variável de ambiente (recomendado):
   ```bash
   export GOOGLE_PLACES_API_KEY="SUA_CHAVE_AQUI"
   ```
2. Ou passe na hora de rodar: `--chave SUA_CHAVE_AQUI`
3. Ou edite a linha `CHAVE_API = ""` no topo do arquivo.

---

## 🛠️ Como criar a chave do Google Places (passo a passo, atualizado)

Você já tem login Google e outras chaves, então é rápido:

1. Acesse **https://console.cloud.google.com/** e selecione (ou crie) um projeto.
2. Ative o faturamento no projeto (o Google exige cartão, mas há **cota grátis mensal**).
3. Menu **APIs e serviços → Biblioteca** → procure por **“Places API (New)”** e clique em **Ativar**.
   > ⚠️ Tem que ser a **“Places API (New)”** (a nova). A antiga “Places API” não atende este app.
4. Vá em **APIs e serviços → Credenciais → Criar credenciais → Chave de API**.
5. Copie a chave (começa com `AIza...`). Pronto — é essa que você cola no app. 🎉

### 🔒 Restrições recomendadas da chave (importante)
Em **Credenciais → sua chave**:
- **Restrições de API:** marque *Restringir chave* e selecione apenas **Places API (New)**.
- **Restrições de aplicativo:**
  - Se for usar o `index.html` direto no navegador → use **Referenciadores HTTP** (ou deixe sem restrição para testar).
  - Se for usar só o Python → pode usar restrição por **endereço IP**.

---

## ▶️ Como usar

### Opção A — App visual (mais fácil)
1. Abra o `index.html` (duplo clique, ou hospede em qualquer servidor estático).
2. Cole a chave, digite a busca (ex.: `salão de beleza na Penha, Rio de Janeiro`).
3. Clique em **🚀 Pesquisar** e depois em **⬇️ CSV** ou **⬇️ JSON**.

### Opção B — Python
```bash
pip install nada   # não precisa: usa só biblioteca padrão do Python 3.10+
export GOOGLE_PLACES_API_KEY="SUA_CHAVE"
python raspador_places.py "salão de beleza na Penha, Rio de Janeiro" --pages 3 --formato ambos
```
Gera `salao-de-beleza-na-penha-rio-de-janeiro.csv` e `.json` na mesma pasta.

---

## ℹ️ Notas úteis
- O Google retorna **no máximo ~60 resultados** por busca (3 páginas de 20). Para pegar mais,
  faça buscas mais específicas por bairro/cidade.
- Nem todo negócio tem telefone ou site cadastrado — esses campos vêm vazios quando não existem.
- Telefone, website e nome fazem parte de SKUs **pagos** da Places API. Confira a
  [cota grátis e os preços](https://developers.google.com/maps/billing-and-pricing/pricing) do Google.
- Use os dados de forma responsável e de acordo com os
  [Termos do Google Maps Platform](https://cloud.google.com/maps-platform/terms).
