import json

from chatbot_platform import cli


def test_upload_then_status(platform, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_platform", lambda: platform)
    source = tmp_path / "chapter one.pdf"
    source.write_bytes(b"%PDF sample")

    cli.main(
        ["upload", str(source), "--course", "STAT 101", "--source-id", "ch1", "--type", "textbook"]
    )
    uploaded = json.loads(capsys.readouterr().out)
    assert uploaded["doc_id"] == "stat_101/ch1"

    cli.main(["status"])
    status = json.loads(capsys.readouterr().out)
    assert status["serving"] is None
    assert status["pending_documents"] == [uploaded["doc_version"]]
