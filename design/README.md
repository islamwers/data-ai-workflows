# Motion design sources

`render.py` generates the two 36-second, 1600×900, 24 fps silent films, posters and GIF previews. English text is built into the frames. All displayed result values come from the local evidence fixtures.

Render after running the two demos. Rendering uses Pillow, NumPy and imageio-ffmpeg 0.6.0. The original render uses the Avenir Next font supplied by macOS; change `FONT` for another environment. No font files are redistributed.

```sh
python3 -m pip install --target .render-deps Pillow numpy imageio-ffmpeg==0.6.0
PYTHONPATH=.render-deps python3 design/render.py
```

Palette: ink `#15364B`, blue `#34749F`, muted `#58758A`, green `#287863`, pale `#E8F2F8`. Six chapters, restrained dissolves, animated state changes and a persistent disclosure footer.
