def run_reminder():

    try:
        df = pd.read_excel("turni.xlsx")

        if df.empty:
            print("Excel vuoto")
            return

        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"]).sort_values("Data")

        riga = df.iloc[0]
        date = riga["Data"].strftime("%Y-%m-%d")

        # =====================
        # UTENTI ATTESI
        # =====================
        expected_users = set()

        for col in df.columns:
            if col == "Data":
                continue

            value = riga[col]
            if pd.isna(value):
                continue

            for nome in str(value).replace(";", ",").split(","):
                nome = nome.strip().lower()
                if nome:
                    expected_users.add(nome)

        # =====================
        # RISPOSTE SOLO PER QUESTO TURNO
        # =====================
        res = supabase.table("responses") \
            .select("*") \
            .eq("date", date) \
            .execute()

        responded_users = {
            r["username"].strip().lower()
            for r in (res.data or [])
            if r.get("status") == "ok"
        }

        non_risposti = expected_users - responded_users

        # =====================
        # MESSAGGIO
        # =====================
        msg = "📢 PROMEMORIA SERVIZIO\n\n"
        msg += "Non hanno ancora confermato:\n\n"

        if not non_risposti:
            msg += "✅ Tutti hanno già confermato"
        else:
            for u in sorted(non_risposti):
                msg += f"{to_tag(u)}\n"

        # =====================
        # BOTTONI
        # =====================
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ OK", "callback_data": f"ok|{date}"}
            ]]
        }

        # =====================
        # INVIO
        # =====================
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "reply_markup": keyboard
            }
        )

        print("📢 Reminder giovedì inviato")

    except Exception as e:
        print("❌ Errore run_reminder:", e)