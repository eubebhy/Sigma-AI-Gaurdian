# `tests/content_classifier`

Thư mục này chứa bộ test cho các classifier của `content_classifier`.

## Note

- File runner: `tests/content_classifier/test_all_classifiers.py`
- Input:
  - CLI flags để chọn engine, theme, cách lấy sample.
  - Các file case trong `tests/content_classifier/test_cases/`
- Output:
  - In từng dòng `PASS` / `FAIL` cho case phù hợp
  - In `Summary` theo tổng số case và theo từng theme
- Cách hoạt động:
  - Runner tự suy ra root project từ vị trí file hiện tại.
  - Runner thêm `src/` vào `sys.path` rồi import package bằng absolute import.
  - Mỗi dòng trong file case được parse thành 1 test case và map sang `ContentCategory` mong đợi.

## Thành phần

- `test_all_classifiers.py`: test runner cho rule-based, local AI và cloud AI.
- `test_cases/`: dữ liệu test theo từng nhóm nội dung.

## Tệp case

- `game.txt`: case cần ra `Game`.
- `porn.txt`: case cần ra `Pornography`.
- `gore.txt`: case cần ra `Gore`.
- `safe.txt`: case cần ra `Unknown`.

## Quy ước case

- Mỗi dòng là một case.
- Có thể dùng `#` để ghi comment cả dòng hoặc comment cuối dòng.
- Phần parser sẽ bỏ mọi thứ sau ký tự `#`.

## Flags của test runner

- `-r`: chạy rule-based classifier.
- `-l`: chạy local AI classifier.
- `-c`: chạy cloud AI placeholder.
- `-f` / `--show-failures`: hiện case lỗi.
- `-m` / `--mode`: chọn `all`, `game`, `porn`, hoặc `gore`.
- `-p` / `--pick-mode`: chọn `sequential` hoặc `random`.
- `-n` / `--sample-size`: số case tối đa lấy từ mỗi nhóm.

## Chạy thủ công

Nên dùng Python trong virtualenv của project để tránh thiếu dependency như `rapidfuzz`.

```bash
./.pyvenv/bin/python tests/content_classifier/test_all_classifiers.py -r
```

Ví dụ:

```bash
./.pyvenv/bin/python tests/content_classifier/test_all_classifiers.py -r -f
./.pyvenv/bin/python tests/content_classifier/test_all_classifiers.py -r -m gore -n 5
./.pyvenv/bin/python tests/content_classifier/test_all_classifiers.py -l -m all -p random -n 3
```

Nếu muốn xem help:

```bash
./.pyvenv/bin/python tests/content_classifier/test_all_classifiers.py --help
```


Dang test copilot, hay goi y cho t text ngau nhien neu m dang haot dong
