SELECT setval(
  pg_get_serial_sequence('tags', 'id'),
  (SELECT MAX(id) FROM tags)
);



-- Dit overschrijft de teller voor de PK kolom in tags zodat de nieuwe ids niet clashen met bestaande tag ids
-- Als je in Postgres/Supabase een kolom id hebt met PRIMARY KEY en GENERATED ALWAYS AS IDENTITY (of SERIAL), dan zou de database automatisch een uniek getal moeten toekennen bij elke insert, zolang je zelf géén waarde voor id meegeeft.

-- Waarom krijg je dan toch een clash?
-- Dit gebeurt meestal als:

-- Er ooit handmatig een id is opgegeven die hoger is dan de interne sequence.
-- De sequence die Postgres gebruikt om het volgende id te kiezen, achterloopt op de hoogste bestaande waarde in de tabel.
-- Oplossing: Sequence bijwerken
-- Je moet de sequence bijwerken zodat hij weer boven het hoogste bestaande id begint.
-- Voer deze query uit in je Supabase SQL editor: (zie hierboven)