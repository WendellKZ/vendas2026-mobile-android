Vendas 2026 - Integração App Android x ERP Web

1) Abra esta pasta do ERP Web no PowerShell.
2) Rode:
   py -3.12 -m pip install -r requirements.txt
3) Inicie o ERP para o app:
   py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --reload --port 5098
   ou dê duplo clique em iniciar_web_para_app_android_5098.bat
4) Teste no navegador do Windows:
   http://localhost:5098/docs
   http://localhost:5098/api/mobile/ping
5) No navegador do emulador Android, teste:
   http://10.0.2.2:5098/api/mobile/ping
6) Depois rode o app Android no Android Studio.

Login local de teste no app:
   usuário: admin
   senha: 123

Observação:
- 10.0.2.2 só funciona dentro do emulador Android.
- No Windows use localhost:5098.
- No celular físico use o IP do PC, exemplo http://192.168.0.50:5098.
