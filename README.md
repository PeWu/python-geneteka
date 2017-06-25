Matches birth, death and marriage records from
[Geneteka](http://geneteka.genealodzy.pl) and creates an HTML output with
links between families.

## Po polsku

Program automatycznie łączy akty małżeństwa, urodzin i zgonów
z [Geneteki](http://geneteka.genealodzy.pl) i produkuje zbiór
stron HTML z odnośnikami pomiędzy rodzinami.

Przykładowy wynik działania programu: http://przodkowie.ml/

### Przykład użycia programów

1. Ściągnięcie danych z Geneteki.
```
python fetch.py 07mz B 944
python fetch.py 07mz S 857
python fetch.py 07mz D 1745
```
Aby wiedzieć, co wpisać jako argumenty wykonania programu, należy
spojrzeć na adres URL podczas wyszukiwania w Genetece,
np. `http://www.geneteka.genealodzy.pl/(...)&bdm=B&w=07mz&rid=944&(...)`
i uruchomić program. Tu przykład dla parafii Klembów – urodzenia,
małżeństwa i zgony.

2. Wstępnie przetworzenie danych
```
python merge.py
```

3. Wygenerowanie plików HTML
```
python generate.py
```
