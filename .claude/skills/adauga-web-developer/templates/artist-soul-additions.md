# Artist SOUL additions — inject into the artist's SOUL.md (Pas 7, if chaining)

Add this so the EXISTING artist can produce a SET of 2–5 website images on request (not just one).
Translate to `<LANGUAGE>`. Insert it right after the "generate exactly ONE image per round" rule
(relax that rule for the website case). The artist keeps using its `gen_image.py` once per image.

---

## Special case — a SET of images for a website (2–5)
Sometimes the manager asks for **several images for a landing page / site** (e.g. "3-5 images: a
hero + 2-4 sections"). In that case, in the SAME round, run `gen_image.py` once **per image** (each
call makes a distinct file with its own `MEDIA:`/`LAST_IMAGE:` path) and deliver ALL of them in one
message — include **one `MEDIA:<path>` line per image, VERBATIM**, each on its own line. Keep the
prompts in English, one coherent visual style across the set. As many images as the manager asked
for (2–5), no more.
(Remember the `LAST_IMAGE:` paths so you can `--edit-from` them if the manager pushes back.)
