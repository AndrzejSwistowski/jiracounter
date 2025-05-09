## Opis
Potrzebujemy zrekonfigurować indeks Elasticsearch używany przez aplikację JiraCounter w celu poprawienia mapowania pól i obsługi języka polskiego.

## Zadania
1. Zainstaluj plugin języka polskiego w Elasticsearch, który zawiera analizator tekstu dla języka polskiego
   - Komenda instalacji: `bin/elasticsearch-plugin install analysis-stempel`
   - Wymagany restart Elasticsearch po instalacji

2. Uruchom skrypt aktualizacji indeksu, który zdefiniuje poprawną strukturę:
   ```bash
   cd e:\Zrodla\jiracounter\jiracouter
   .venv\Scripts\python.exe recreate_es_index.py --confirm --resync --days 30
   ```

3. Zweryfikuj, czy indeks został prawidłowo utworzony:
   - Sprawdź w Kibana pod adresem http://elastic.voyager.pl:5601
   - Przejdź do zakładki "Stack Management" > "Index Management"
   - Indeks "jira-changelog" powinien być widoczny z poprawnym mapowaniem

4. Upewnij się, że analizator języka polskiego działa poprawnie:
   - W Kibana przejdź do "Dev Tools"
   - Wykonaj zapytanie testowe:
   ```
   POST jira-changelog/_analyze
   {
     "analyzer": "polish",
     "text": "Testowy tekst w języku polskim do analizy"
   }
   ```

## Uwagi techniczne
- Obecne problemy związane są z brakiem obsługi języka polskiego w standardowym Elasticsearch
- Aplikacja używa mapowania pól tekstowych z analizatorem języka polskiego
- W przypadku problemów z instalacją pluginu, można zmodyfikować plik `es_mapping.py`, aby używał standardowego analizatora tekstu
