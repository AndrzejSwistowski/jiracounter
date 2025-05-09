# Rekonfiguracja indeksu Elasticsearch dla JiraCounter

## Opis
Potrzebujemy zrekonfigurować indeks Elasticsearch używany przez aplikację JiraCounter w celu poprawienia mapowania pól. Obecnie występują problemy z przeszukiwaniem tekstu w języku polskim.

## Zadania
1. Wykonaj poniższy skrypt bash aby skonfigurować indeks Elasticsearch z poprawną obsługą języka polskiego:

```bash
#!/bin/bash
# Skrypt do konfiguracji indeksu Elasticsearch z obsługą języka polskiego

# Parametry połączenia - dostosuj w razie potrzeby
ES_HOST="elastic.voyager.pl"
ES_PORT="9200"
ES_URL="http://${ES_HOST}:${ES_PORT}"

# Usuń istniejący indeks
echo "Usuwanie istniejącego indeksu jira-changelog..."
curl -s -X DELETE "${ES_URL}/jira-changelog"

# Utwórz indeks z poprawnym mapowaniem i analizatorem języka polskiego
echo "Tworzenie indeksu jira-changelog z poprawnym mapowaniem..."
curl -X PUT "${ES_URL}/jira-changelog" -H 'Content-Type: application/json' -d '{
  "settings": {
    "analysis": {
      "analyzer": {
        "polish": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "polish_stop"]
        }
      },
      "filter": {
        "polish_stop": {
          "type": "stop",
          "stopwords": "_polish_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "historyId": {"type": "keyword"},
      "historyDate": {"type": "date"},
      "@timestamp": {"type": "date"},
      "factType": {"type": "integer"},
      "issue": {
        "properties": {
          "key": {"type": "keyword"},
          "type": { 
            "properties": {
              "name": {"type": "keyword"}
            }
          },
          "status": {
            "properties": {
              "name": {"type": "keyword"},
              "change_date": {"type": "date"}
            }
          },
          "created_at": {"type": "date"}
        }
      },
      "allocation": {"type": "keyword"},
      "labels": {"type": "keyword"}, 
      "components": {"type": "keyword"}, 
      "summary": {
        "type": "text", 
        "analyzer": "standard",
        "fields": {
          "keyword": {"type": "keyword"},
          "polish": {"type": "text", "analyzer": "polish"}
        }
      },
      "project": {
        "properties": {
          "key": {"type": "keyword"}
        }
      },
      "parent_issue": {
        "properties": {
          "key": {"type": "keyword"},
          "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        }
      },
      "epic_issue": {
        "properties": {
          "key": {"type": "keyword"},
          "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        }
      },
      "author": {
        "properties": {
          "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        }
      },
      "reporter": {
        "properties": {
          "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        }
      },
      "days_since_creation": {"type": "float"},
      "todo_exit_date": {"type": "date"},
      "changes": {
        "type": "nested",
        "properties": {
          "field": {"type": "keyword"},
          "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        }
      },
      "description_text": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {"type": "keyword", "ignore_above": 32766},
          "english": {"type": "text", "analyzer": "english"},
          "polish": {"type": "text", "analyzer": "polish"}
        }
      },
      "comment_text": {
        "type": "text", 
        "analyzer": "standard",
        "fields": {
          "keyword": {"type": "keyword", "ignore_above": 32766},
          "english": {"type": "text", "analyzer": "english"},
          "polish": {"type": "text", "analyzer": "polish"}
        }
      }
    }
  }
}'

# Sprawdź, czy indeks został utworzony
echo "Sprawdzanie czy indeks został utworzony..."
curl -s "${ES_URL}/_cat/indices/jira-changelog"

# Test analizatora języka polskiego
echo "Testowanie analizatora języka polskiego..."
curl -X POST "${ES_URL}/jira-changelog/_analyze" -H 'Content-Type: application/json' -d '{
  "analyzer": "polish",
  "text": "Testowy tekst w języku polskim"
}'
```

2. Po wykonaniu skryptu i poprawnym utworzeniu indeksu, zweryfikuj:
   - Czy indeks "jira-changelog" został poprawnie utworzony
   - Czy test analizatora języka polskiego zwraca poprawnie podzielone tokeny

3. Poinformuj zespół deweloperski o wykonaniu zadania, aby mogli przeprowadzić pełną synchronizację danych

## Weryfikacja zadania
Wykonaj poniższe zapytanie w Kibana (zakładka Dev Tools) aby sprawdzić poprawność konfiguracji:

```
GET jira-changelog/_search
{
  "size": 0,
  "aggs": {
    "indices": {
      "terms": {
        "field": "project.key",
        "size": 10
      }
    }
  }
}
```

Powinno zwrócić listę projektów w indeksie.

## Uwagi techniczne
- W przypadku problemów z wykonaniem skryptu, można go wykonać ręcznie krok po kroku w interfejsie Kibana (Dev Tools)
- Analizator języka polskiego został uproszczony do tokenizacji i usuwania tzw. "stop words" (przyimków, spójników itd.)
- Aplikacja po ponownym uruchomieniu automatycznie pobierze dane z JIRA i zindeksuje je

## Priorytet
Wysoki - blokuje poprawne wyszukiwanie i analizę tekstów w języku polskim

## Termin realizacji
Do końca bieżącego tygodnia
