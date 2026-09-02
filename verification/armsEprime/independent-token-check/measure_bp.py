# -*- coding: utf-8 -*-
"""Independent token-length measurement of BP.md vs BP-sec.md.

Split each file at the character following "。" into sentences (expect 4 each),
encode with the Qwen3-30B-A3B-Instruct-2507 tokenizer (add_special_tokens=False),
and check whether each paraphrased sentence falls within +-10% of the original.
"""
import io
import json
import sys

SRC_PATH = r"C:\Users\PC\Desktop\Ryokai-OS-Verification\proposals\addendum-Eprime\BP.md"
SEC_PATH = r"C:\Users\PC\Desktop\Ryokai-OS-Verification\proposals\addendum-Eprime\BP-sec.md"
MODEL_ID = "Qwen/Qwen3-30B-A3B-Instruct-2507"


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_sentences(text):
    """Split immediately after each '。'. Keep the '。'. Drop empty/whitespace-only pieces."""
    out = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch == "\u3002":  # 。
            out.append("".join(buf))
            buf = []
    tail = "".join(buf)
    if tail.strip():
        out.append(tail)
    return [s.strip() for s in out if s.strip()]


def main():
    src_raw = read_text(SRC_PATH)
    sec_raw = read_text(SEC_PATH)
    src_sents = split_sentences(src_raw)
    sec_sents = split_sentences(sec_raw)

    sys.stderr.write("src sentence count: %d\n" % len(src_sents))
    sys.stderr.write("sec sentence count: %d\n" % len(sec_sents))

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    def n_tok(s):
        return len(tok.encode(s, add_special_tokens=False))

    n = min(len(src_sents), len(sec_sents))
    sentences = []
    all_within = True
    tot_src = 0
    tot_sec = 0
    for i in range(n):
        a = src_sents[i]
        b = sec_sents[i]
        ta = n_tok(a)
        tb = n_tok(b)
        lo = int(round(ta * 0.9))
        hi = int(round(ta * 1.1))
        within = bool(lo <= tb <= hi)
        if not within:
            all_within = False
        tot_src += ta
        tot_sec += tb
        sentences.append({
            "n": i + 1,
            "src": a,
            "sec": b,
            "src_tok": ta,
            "sec_tok": tb,
            "lo": lo,
            "hi": hi,
            "within_10pct": within,
        })

    result = {
        "measurer": "independent",
        "tokenizer": getattr(tok, "name_or_path", MODEL_ID),
        "vocab_size": len(tok),
        "tokenizer_class": type(tok).__name__,
        "sentences": sentences,
        "total": {
            "src_tok": tot_src,
            "sec_tok": tot_sec,
            "ratio": round(tot_sec / float(tot_src), 4) if tot_src else 0.0,
        },
        "all_within": all_within,
    }

    # extra diagnostics to stderr only (not part of the JSON contract)
    sys.stderr.write("vocab_size attr: %s ; len(tok): %s\n" % (getattr(tok, "vocab_size", None), len(tok)))
    sys.stderr.write("whole-file tokens: src=%d sec=%d\n" % (n_tok(src_raw.strip()), n_tok(sec_raw.strip())))

    out = json.dumps(result, ensure_ascii=False, indent=1)
    with io.open(r"C:\Users\PC\AppData\Local\Temp\claude\C--Users-PC\e68bb0c9-a40a-47dc-ac76-9f369fc68a81\scratchpad\result.json", "w", encoding="utf-8") as f:
        f.write(out)
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
