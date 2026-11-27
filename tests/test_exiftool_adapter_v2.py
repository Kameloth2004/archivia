"""TEST-ONLY: adaptador universal sem downloads ou execução real de ExifTool."""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from archivia.metadata.exiftool_adapter import extract_exiftool


class ExifToolAdapterTests(unittest.TestCase):
    def test_groups_unknown_gps_xmp_and_duplicates_are_not_filtered(self):
        record = [{
            "File:FileName": "imagem.jpg",
            "GPS:GPSLatitude": "27 deg 35 min S",
            "XMP-dc:Creator": ["Autor", "Editor"],
            "MakerNotes:Unknown_987": "Identificador profissional",
            "ICC_Profile:ProfileDescription": "Adobe RGB (1998)",
        }]
        response = subprocess.CompletedProcess(
            args=["exiftool"], returncode=0,
            stdout=json.dumps(record).encode("utf-8"), stderr=b"",
        )
        with patch(
            "archivia.metadata.exiftool_adapter.subprocess.run",
            return_value=response,
        ) as execute:
            groups = extract_exiftool(Path("imagem.jpg"), "exiftool")
        by_group = {g["name"]: dict(g["fields"]) for g in groups}
        self.assertEqual(by_group["GPS"]["GPSLatitude"], "27 deg 35 min S")
        self.assertEqual(by_group["XMP-dc"]["Creator"], ["Autor", "Editor"])
        self.assertEqual(
            by_group["MakerNotes"]["Unknown_987"],
            "Identificador profissional",
        )
        args = execute.call_args.args[0]
        self.assertIn("-a", args)
        self.assertIn("-U", args)
        self.assertIn("-ee", args)
        self.assertIn("-struct", args)
        self.assertIn("-j", args)
        self.assertEqual(execute.call_args.kwargs["shell"], False)
        self.assertGreater(execute.call_args.kwargs["timeout"], 0)

    def test_invalid_json_and_timeouts_fail_explicitly(self):
        with patch(
            "archivia.metadata.exiftool_adapter.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"{not valid json}",
                stderr=b"",
            ),
        ):
            with self.assertRaises(ValueError):
                extract_exiftool(Path("invalid.pdf"), "exiftool")
        with patch(
            "archivia.metadata.exiftool_adapter.subprocess.run",
            side_effect=subprocess.TimeoutExpired("exiftool", 15),
        ):
            with self.assertRaises(RuntimeError):
                extract_exiftool(Path("slow.pdf"), "exiftool")


if __name__ == "__main__":
    unittest.main()
