# osess — export Ollama desktop

![python](https://img.shields.io/badge/python-3.8%2B-blue) ![sqlite](https://img.shields.io/badge/sqlite-orange) ![ollama](https://img.shields.io/badge/ollama-client-blue) ![license](https://img.shields.io/badge/license-Apache--2.0-blue)

`osess.py` est un petit utilitaire en CLI qui snapshotte la base SQLite
d'Ollama Desktop, liste les conversations et exporte une session en
Markdown.

## Pré-requis

- Python 3.8+
- Ollama Desktop installé et ayant déjà créé une base de conversations
- Aucune dépendance externe (stdlib uniquement)

## Compatibilité

| OS         | Chemin de la base cliente                          |
|------------|----------------------------------------------------|
| Windows    | `%LOCALAPPDATA%\Ollama\db.sqlite` (ou `%APPDATA%`) |
| Linux      | `~/.ollama/db.sqlite`                              |
| macOS      | `~/.ollama/db.sqlite`                              |

Si Ollama a été installé à un emplacement non standard, le script ne
trouvera pas la base. Arrêtez le client Ollama, puis copiez manuellement
`db.sqlite` dans ce dossier avant de relancer.

## Installation

```bash
git clone https://github.com/TryTheRedOne/ollama_export.git
cd ollama_export
```

## Utilisation

```bash
# 1. Récupérer une copie de la base cliente dans ./db.sqlite
python osess.py pull            # demande confirmation si copie existante
python osess.py pull -y         # force l'écrasement (scripts)

# 2. Lister les sessions (numéro, id, nb messages, date, titre)
python osess.py list

# 3. Exporter une session en .md (id ou préfixe d'id affiché par 'list')
python osess.py export a1b2c3d4
python osess.py export a1b2c3d4 -o sortie.md
```

## Fichiers

| Fichier        | Rôle                                              |
|----------------|---------------------------------------------------|
| `osess.py`     | Le script                                         |
| `db.sqlite`    | Copie locale de la base (gitignorée)              |
| `LICENSE`      | Licence Apache 2.0                                |
| `.gitignore`   | Ignore `db.sqlite*` et les exports `.md`          |

## Format d'export

Un fichier `slug-du-titre-AAAAMMJJ-HHMM.md` contenant le titre, l'id
de session, dates, et les messages user/assistant formatés en Markdown.

## Disclaimer

- **Lecture seule** : le script effectue une copie de la base cliente
  via `sqlite3.backup` et ne modifie jamais la base source.
- **Arrêt du client** : pour une copie cohérente, il est recommandé
  d'arrêter le client Ollama avant `pull` (évite les écritures
  concurrentes).
- **Aucune garantie** : ce logiciel est fourni « tel quel », sans
  garantie d'aucune sorte. L'auteur ne saurait être tenu responsable
  d'éventuels incidents (perte de données, corruption, etc.) liés à
  son utilisation.