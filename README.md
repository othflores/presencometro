# Presençômetro · 3ºC TDS

Sistema de registro de presença com geolocalização — Colégio Adaile Maria Leite, Maringá - PR.

## 🚀 Como rodar

```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://localhost:5000

## 📱 PWA (Progressive Web App)

O sistema pode ser instalado como aplicativo no celular:
- **Android (Chrome):** toque no banner "⬇ instalar" ou menu → "Adicionar à tela inicial"
- **iOS (Safari):** compartilhar → "Adicionar à Tela de Início"

## 📡 API REST

Todos os endpoints abaixo retornam JSON.

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Status do servidor |
| GET | `/api/sessions` | Lista todas as sessões |
| POST | `/api/session/new` | Cria uma nova sessão |
| GET | `/api/session/<id>` | Detalhes de uma sessão |
| POST | `/api/session/<id>/close` | Encerra uma sessão |
| GET | `/api/session/<id>/records` | Lista presenças |
| GET | `/api/session/<id>/export` | Exporta CSV |
| POST | `/api/checkin` | Registra presença |

### POST `/api/session/new`
```json
{
  "name": "Aula de Algoritmos",
  "radius": 100,
  "lat": -23.4215,
  "lon": -51.9331,
  "address": "Maringá, PR"
}
```

### POST `/api/checkin`
```json
{
  "session_id": "1718000000000",
  "name": "João Silva",
  "lat": -23.4215,
  "lon": -51.9331
}
```

## 📁 Estrutura

```
presencometro_tematico/
├── app.py                  # Backend Flask + API REST
├── requirements.txt
├── data/
│   └── attendance.json     # Dados persistidos localmente
├── static/
│   ├── offline.html        # Fallback offline (PWA)
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
└── templates/
    ├── base.html           # Layout base + PWA boilerplate
    ├── index.html          # Página inicial
    ├── session.html        # Sessão individual
    └── credits.html
```

## ✨ Melhorias v2

- **PWA completa:** instalável no Android/iOS, funciona offline
- **API REST estruturada:** prefixo `/api/`, respostas padronizadas com `{ok, ...}`
- **QR Code:** gera QR para compartilhar link da sessão
- **Busca em tempo real:** filtre presenças por nome
- **Compartilhamento nativo:** Web Share API no mobile
- **GPS contínuo:** `watchPosition` em vez de `getCurrentPosition`
- **Detecção offline:** banner automático quando sem conexão
- **Service Worker:** cache inteligente + fallback offline
- **UX mobile:** inputs otimizados, safe-areas para notch, tap highlight removido
- **Validação de duplicatas:** impede o mesmo aluno registrar duas vezes
- **Export CSV com nome da sessão** no filename
