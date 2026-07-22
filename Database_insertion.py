import json
import psycopg2

Db_config = {
    "dbname": "bmi_data",
    "user": "postgres",
    "password": "974029",
    "host": "localhost",
    "port": "5432"
}

def job_import():
    with open("jobs_scraped.json", "r", encoding = "utf-8") as f:
        data = json.load(f)

    conn = psycopg2.connect(**Db_config)
    cursor = conn.cursor()

    ### In order to understand the insertion order, pgAdmin4 was used to get a visual representation of how the database is connected.
    # Using that visualization, the code has been written with those connections in mind.
    try:
        for item in data:
            # element: dienststelle
            cursor.execute(
                "INSERT INTO public.dienststelle (dienststelle_name) VALUES (%s) RETURNING id_dienststelle;",
                (item["Base Data"]["Dienststelle"],)
            )
            id_dienststelle = cursor.fetchone()[0]

            # element: einstufung
            cursor.execute(
                "INSERT INTO public.einstufung (derzeit_neu, beantragt) VALUES (%s, %s) RETURNING id_einstufung;",
                (item["Base Data"]["Wertigkeit/Einstufung"], "k.A.")
            )
            id_einstufung = cursor.fetchone()[0]
            
            # element: organisationseinheit
            # Problem: Unique ID has the organiational unit as abbreviation, so that is used
            cursor.execute(
                "INSERT INTO public.organisationseinheit (sektion, id_dienststelle) VALUES (%s, %s) RETURNING id_organisationseinheit;",
                (item["Unique_ID"].split("-")[0], id_dienststelle)
            )
            id_organisationseinheit = cursor.fetchone()[0]

            # element: arbeitsplatz
            job_title = item.get("Job Title ") or item.get("Job Title") or "k.A"
            cursor.execute(
                """
                INSERT INTO public.arbeitsplatz (id_organisationseinheit, id_dienststelle, id_einstufung, funktion, arbeitsplatz_beschreibung, vertritt_wen, wird_vertreten_von)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_arbeitsplatz;
                """,
                (id_organisationseinheit, id_dienststelle, id_einstufung, job_title, item["Job General Summary"], "k.A", "k.A")
            )
            id_arbeitsplatz = cursor.fetchone()[0]

            # element: anforderungen
            cursor.execute(
                "INSERT INTO public.anforderungen (anforderung) VALUES (%s) RETURNING id_anforderung;",
                (item["Requirements"],)
            )
            id_anforderung = cursor.fetchone()[0]

            # element: besoldung
            cursor.execute(
                "INSERT INTO public.besoldung (verwendungsgruppe, id_arbeitsplatz) VALUES (%s, %s) RETURNING id_besoldung;",
                (item["Base Data"]["Monatsentgelt/bezug"], id_arbeitsplatz)
            )
            #id_besoldung = cursor.fetchone()[0]

            # element: arbeitsplatz_anforderung
            cursor.execute(
                "INSERT INTO public.arbeitsplatz_anforderung (id_arbeitsplatz, id_anforderung) VALUES (%s, %s) RETURNING id_arbeitsplatz_anforderung;",
                (id_arbeitsplatz, id_anforderung)
            )

            # element: aufgabe
            cursor.execute(
                "INSERT INTO public.aufgabe (beschreibung, id_arbeitsplatz) VALUES (%s, %s) RETURNING id_aufgabe;",
                (item["Job activites"], id_arbeitsplatz)
            )

            # element: taetigkeiten
            cursor.execute(
                "INSERT INTO public.taetigkeiten (beschreibung, id_arbeitsplatz) VALUES (%s, %s) RETURNING id_taetigkeiten;",
                (item["Job General Summary"], id_arbeitsplatz)
            )

        conn.commit()
        print("Sucessfully imported all jobs")

    except Exception as e:
        conn.rollback()
        print(f"Error when parsing data into DB: {e}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    job_import()