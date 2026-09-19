"""Serving a web build of Rau to Chrome, shared by the browser benchmarks."""

import http.server
import os
import sys
import threading
from pathlib import Path

rau_dir = Path(__file__).parent.parent.parent / "rau"

# Projects are served from a local folder under a made-up repository, as if
# they were on GitHub.
CORS = {"Access-Control-Allow-Origin": "*", "Cross-Origin-Resource-Policy": "cross-origin"}


class Site(http.server.SimpleHTTPRequestHandler):
    """The web build laid out as the deploy does, `web/` with `assets/` beside
    it, cross-origin isolated like the live site, and cached for good so a load
    never asks again."""

    def translate_path(self, path):
        self.directory = str(rau_dir if path.startswith("/assets/") else rau_dir / "web")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "max-age=31536000, immutable")
        super().end_headers()

    def log_message(self, *args):
        pass


def start():
    """The address of the page RAU_SITE points at, or else of the build
    `./web/build-web.sh` leaves in the Rau repository next to this one, served
    from here so no load reaches the network."""
    if site := os.environ.get("RAU_SITE"):
        return site

    if not (rau_dir / "web" / "pkg" / "rau_bg.wasm").exists():
        sys.exit(f"No web build in {rau_dir}, run ./web/build-web.sh there first")

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Site)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/"


def serve_project(context, folder):
    """Answer the GitHub tree and file requests of the `local/projects`
    repository from the folder's parent, with only `folder` in the tree, and
    return the query that creates the project from it into IndexedDB."""
    root = folder.parent
    files = [p for p in folder.rglob("*") if p.is_file()]
    tree = [{"path": p.relative_to(root).as_posix(), "type": "blob"} for p in files]

    context.route(
        "https://api.github.com/repos/local/projects/**",
        lambda route: route.fulfill(json={"tree": tree}, headers=CORS),
    )
    context.route(
        "https://raw.githubusercontent.com/local/projects/main/**",
        lambda route: route.fulfill(
            path=root / route.request.url.split("/local/projects/main/", 1)[1],
            headers=CORS,
        ),
    )

    return (
        f"?action=new&storage=persistent&project={folder.name}"
        f"&owner=local&repo=projects&ref=main&path={folder.name}"
    )
