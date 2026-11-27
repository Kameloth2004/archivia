"""TEST-ONLY: interpretação XMP e acesso ao XML original sem escrita."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from support import temporary_test_directory

from archivia.metadata.xmp_reader import parse_xmp, xmp_from_image_info
from archivia.metadata.reader import read_file_metadata, format_metadata_report

_XMP = '''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.5.0">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:exif="http://ns.adobe.com/exif/1.0/"
      xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      exif:DateTimeOriginal="2025-11-24T01:06:30+00:00"
      Iptc4xmpExt:DigitalSourceFileType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia">
      <dc:title><rdf:Alt>
        <rdf:li xml:lang="pt-BR">Título profissional para SEO e GEO</rdf:li>
      </rdf:Alt></dc:title>
      <dc:creator><rdf:Seq><rdf:li>Autor original</rdf:li></rdf:Seq></dc:creator>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''


class XmpMetadataTests(unittest.TestCase):
    def test_structured_values_are_not_hex_or_truncated(self):
        groups, original = parse_xmp(_XMP.encode("utf-8"))
        fields = dict(groups[0]["fields"])
        self.assertEqual(fields["exif:DateTimeOriginal"], "2025-11-24T01:06:30+00:00")
        self.assertIn("trainedAlgorithmicMedia", fields["Iptc4xmpExt:DigitalSourceFileType"])
        self.assertIn("Título profissional", str(fields))
        self.assertIn("Autor original", str(fields))
        self.assertIn("trainedAlgorithmicMedia", original["text"])
        self.assertIn("<?xpacket", original["text"])
        self.assertNotIn("hex:", str(fields))

    def test_no_whitelist_for_custom_xmp_fields(self):
        xml = (
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:custom="urn:archivia:test">'
            '<rdf:Description custom:PrivateKey="VISIBLE" '
            'custom:UnknownTag="123" /></rdf:RDF>'
        )
        groups, _ = parse_xmp(xml)
        fields = dict(groups[0]["fields"])
        self.assertEqual(fields["custom:PrivateKey"], "VISIBLE")
        self.assertEqual(fields["custom:UnknownTag"], "123")

    def test_dtd_entities_are_rejected_but_raw_is_preserved(self):
        malicious = '<!DOCTYPE x [<!ENTITY secret SYSTEM "file:///etc/passwd">]><x>&secret;</x>'
        with self.assertRaises(ValueError):
            parse_xmp(malicious)
        groups, raw, warnings = xmp_from_image_info({"xmp": malicious})
        self.assertFalse(groups)
        self.assertTrue(warnings)
        self.assertEqual(raw[0]["text"], malicious)

    def test_real_png_pillow_reader_decodes_structured_xmp_and_preserves_raw(self):
        try:
            from PIL import Image, PngImagePlugin
        except ImportError:
            self.skipTest("Pillow opcional não instalado")
        with temporary_test_directory() as folder:
            path = folder / "xmp_profissional.png"
            image = Image.new("RGB", (8, 8), "blue")
            png_info = PngImagePlugin.PngInfo()
            png_info.add_itxt("XML:com.adobe.xmp", _XMP)
            image.save(path, "PNG", pnginfo=png_info)
            before = path.read_bytes()
            with patch("archivia.metadata.reader.available_exiftool", return_value=None):
                payload = read_file_metadata(path)
            report = format_metadata_report(payload)
            self.assertIn("Iptc4xmpExt:DigitalSourceFileType", report)
            self.assertIn("trainedAlgorithmicMedia", report)
            self.assertIn("2025-11-24T01:06:30+00:00", report)
            self.assertNotIn("hex: 3c 3f 78", report)
            self.assertTrue(payload.get("raw_sections"))
            self.assertIn("<?xpacket", payload["raw_sections"][0]["text"])
            self.assertEqual(before, path.read_bytes())

    def test_xmp_size_limit_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "2 MiB"):
            parse_xmp(b"<x>" + b"1" * (2 * 1024 * 1024) + b"</x>")


if __name__ == "__main__":
    unittest.main()
