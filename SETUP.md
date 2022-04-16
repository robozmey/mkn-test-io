## Первоначальная настройка системы (Ubuntu Linux)

В качестве тестирующей системы используется компонент системы сборки ПО [dune](https://dune.build/). Для того, чтобы её настроить, необходимо выполнить следующие действия:

0. Установить базовый инструментарий для работы на курсе (с большой вероятностью это всё уже установлено):

```
sudo apt update
sudo apt install build-essential
sudo apt install git-all
```

1. Установить менеджер пакетов [opam](https://opam.ocaml.org/):

```
sudo add-apt-repository ppa:avsm/ppa
sudo apt update
sudo apt install opam
```

2. Настроить окружение:

```
opam init
opam switch -y create ./ --deps-only --with-test ocaml-base-compiler.4.12.0
```
В процессе вам могут задавать разные вопросы, стоит на всё соглашаться (`y`).

3. Установить `dune`:

```
opam install dune.2.9.0
```
