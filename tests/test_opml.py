"""
Tests for brepodder.services.opml module.
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))

from services.opml import Exporter, Importer


class TestExporter:
    """Tests for OPML Exporter class."""

    def test_filename_gets_opml_extension(self, tmp_path):
        """Should add .opml extension if not present."""
        exporter = Exporter(str(tmp_path / "subscriptions"))
        assert exporter.filename.endswith(".opml")

    def test_filename_keeps_opml_extension(self, tmp_path):
        """Should keep .opml extension if already present."""
        exporter = Exporter(str(tmp_path / "subs.opml"))
        assert exporter.filename == str(tmp_path / "subs.opml")

    def test_filename_keeps_xml_extension(self, tmp_path):
        """Should keep .xml extension if present."""
        exporter = Exporter(str(tmp_path / "subs.xml"))
        assert exporter.filename == str(tmp_path / "subs.xml")

    def test_write_creates_file(self, tmp_path):
        """Should create OPML file with channels."""
        filepath = str(tmp_path / "test.opml")
        exporter = Exporter(filepath)
        
        channels = [
            (1, "Podcast One", "https://example.com/feed1.xml", "https://example.com", "First podcast", "logo1.png", "logobig1.png"),
        ]
        
        result = exporter.write(channels)
        
        assert result is True
        assert os.path.exists(filepath)

    def test_write_contains_opml_structure(self, tmp_path):
        """Should create valid OPML structure."""
        filepath = str(tmp_path / "test.opml")
        exporter = Exporter(filepath)
        
        channels = [
            (1, "Test Podcast", "https://example.com/feed.xml", "https://example.com", "Description", "logo.png", "logobig.png"),
        ]
        
        exporter.write(channels)
        
        with open(filepath, "rb") as f:
            content = f.read().decode("utf-8")
        
        assert '<?xml version="1.0" encoding="utf-8"?>' in content
        assert '<opml version="1.1">' in content
        assert "<head>" in content
        assert "<body>" in content
        assert "brePodder subscriptions" in content

    def test_write_contains_channel_data(self, tmp_path):
        """Should include channel attributes in outline."""
        filepath = str(tmp_path / "test.opml")
        exporter = Exporter(filepath)
        
        channels = [
            (1, "My Podcast", "https://feed.example.com/rss", "https://example.com", "Great podcast", "logo.png", "logobig.png"),
        ]
        
        exporter.write(channels)
        
        with open(filepath, "rb") as f:
            content = f.read().decode("utf-8")
        
        assert 'title="My Podcast"' in content
        assert 'xmlUrl="https://feed.example.com/rss"' in content
        assert 'text="Great podcast"' in content
        assert 'type="rss"' in content

    def test_write_multiple_channels(self, tmp_path):
        """Should handle multiple channels."""
        filepath = str(tmp_path / "test.opml")
        exporter = Exporter(filepath)
        
        channels = [
            (1, "Podcast A", "https://a.com/feed.xml", "https://a.com", "Desc A", "logo.png", "logobig.png"),
            (2, "Podcast B", "https://b.com/feed.xml", "https://b.com", "Desc B", "logo.png", "logobig.png"),
            (3, "Podcast C", "https://c.com/feed.xml", "https://c.com", "Desc C", "logo.png", "logobig.png"),
        ]
        
        result = exporter.write(channels)
        
        assert result is True
        with open(filepath, "rb") as f:
            content = f.read().decode("utf-8")
        
        assert 'title="Podcast A"' in content
        assert 'title="Podcast B"' in content
        assert 'title="Podcast C"' in content

    def test_write_empty_channels(self, tmp_path):
        """Should handle empty channel list."""
        filepath = str(tmp_path / "test.opml")
        exporter = Exporter(filepath)
        
        result = exporter.write([])
        
        assert result is True
        assert os.path.exists(filepath)

    def test_write_returns_false_on_permission_error(self, tmp_path):
        """Should return False when write fails."""
        exporter = Exporter("/nonexistent/path/file.opml")
        
        result = exporter.write([])
        
        assert result is False

    def test_create_node(self, tmp_path):
        """Should create XML element with text content."""
        import xml.dom.minidom
        exporter = Exporter(str(tmp_path / "test.opml"))
        doc = xml.dom.minidom.Document()
        
        node = exporter.create_node(doc, "title", "Test Title")
        
        assert node.tagName == "title"
        assert node.firstChild.nodeValue == "Test Title"

    def test_create_outline(self, tmp_path):
        """Should create outline element with channel attributes."""
        import xml.dom.minidom
        exporter = Exporter(str(tmp_path / "test.opml"))
        doc = xml.dom.minidom.Document()
        
        channel = (1, "Podcast", "https://feed.url", "https://home.url", "Description", "logo", "logobig")
        outline = exporter.create_outline(doc, channel)
        
        assert outline.tagName == "outline"
        assert outline.getAttribute("title") == "Podcast"
        assert outline.getAttribute("xmlUrl") == "https://feed.url"
        assert outline.getAttribute("text") == "Description"
        assert outline.getAttribute("type") == "rss"


class TestImporter:
    """Tests for OPML Importer class."""

    def test_import_from_local_file(self, tmp_path, sample_opml_content):
        """Should import channels from local OPML file."""
        opml_file = tmp_path / "subscriptions.opml"
        opml_file.write_text(sample_opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert len(model) == 2
        assert model[0]["title"] == "Podcast One"
        assert model[0]["url"] == "https://example.com/feed1.xml"
        assert model[1]["title"] == "Podcast Two"

    def test_import_extracts_url(self, tmp_path, sample_opml_content):
        """Should extract xmlUrl from outline."""
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(sample_opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model[0]["url"] == "https://example.com/feed1.xml"
        assert model[1]["url"] == "https://example.com/feed2.xml"

    def test_import_strips_whitespace(self, tmp_path):
        """Should strip whitespace from attributes."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline title="  Spaced Title  " text="  Spaced Text  " 
                 xmlUrl="  https://example.com/feed.xml  " type="rss"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model[0]["title"] == "Spaced Title"
        assert model[0]["url"] == "https://example.com/feed.xml"

    def test_import_uses_text_as_title_fallback(self, tmp_path):
        """Should use text attribute if title is missing."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline text="Text as Title" xmlUrl="https://example.com/feed.xml" type="rss"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model[0]["title"] == "Text as Title"

    def test_import_uses_url_as_title_fallback(self, tmp_path):
        """Should use URL as title if both title and text are missing."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline xmlUrl="https://example.com/feed.xml" type="rss"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model[0]["title"] == "https://example.com/feed.xml"

    def test_import_skips_invalid_types(self, tmp_path):
        """Should skip outlines with invalid type."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline title="Valid" xmlUrl="https://valid.com/feed.xml" type="rss"/>
        <outline title="Invalid" xmlUrl="https://invalid.com/feed.xml" type="atom"/>
        <outline title="Also Valid" xmlUrl="https://valid2.com/feed.xml" type="link"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert len(model) == 2
        titles = [m["title"] for m in model]
        assert "Valid" in titles
        assert "Also Valid" in titles
        assert "Invalid" not in titles

    def test_import_skips_without_xmlurl(self, tmp_path):
        """Should skip outlines without xmlUrl."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline title="No URL" type="rss"/>
        <outline title="Has URL" xmlUrl="https://example.com/feed.xml" type="rss"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert len(model) == 1
        assert model[0]["title"] == "Has URL"

    def test_import_from_url(self, sample_opml_content, mocker):
        """Should import from HTTP URL."""
        mock_response = MagicMock()
        mock_response.content = sample_opml_content.encode("utf-8")
        mocker.patch("requests.get", return_value=mock_response)
        
        importer = Importer("https://example.com/subscriptions.opml")
        model = importer.get_model()
        
        assert len(model) == 2

    def test_import_handles_connection_error(self, mocker):
        """Connection errors in read_url result in empty content, causing XML parse error."""
        import requests
        import xml.parsers.expat
        mocker.patch("services.opml.requests.get", side_effect=requests.exceptions.ConnectionError())
        
        # Connection error returns empty string from read_url
        # The XML parser then raises an error on empty content
        # This is expected behavior - the error is logged but propagated
        with pytest.raises(xml.parsers.expat.ExpatError):
            Importer("https://example.com/subs.opml")

    def test_import_handles_http_error(self, mocker):
        """HTTP errors in read_url result in empty content, causing XML parse error."""
        import requests
        import xml.parsers.expat
        mocker.patch("services.opml.requests.get", side_effect=requests.exceptions.HTTPError())
        
        # HTTP error returns empty string from read_url
        # The XML parser then raises an error on empty content
        # This is expected behavior - the error is logged but propagated
        with pytest.raises(xml.parsers.expat.ExpatError):
            Importer("https://example.com/subs.opml")

    def test_import_empty_opml(self, tmp_path):
        """Should handle OPML with no outlines."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body></body>
</opml>'''
        opml_file = tmp_path / "empty.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model == []

    def test_get_model_returns_list(self, tmp_path, sample_opml_content):
        """Should return a list from get_model."""
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(sample_opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert isinstance(model, list)

    def test_description_differs_from_title(self, tmp_path):
        """Should use URL as description if text equals title."""
        opml_content = '''<?xml version="1.0"?>
<opml version="1.1">
    <body>
        <outline title="Same" text="Same" xmlUrl="https://example.com/feed.xml" type="rss"/>
    </body>
</opml>'''
        opml_file = tmp_path / "subs.opml"
        opml_file.write_text(opml_content)
        
        importer = Importer(str(opml_file))
        model = importer.get_model()
        
        assert model[0]["title"] == "Same"
        assert model[0]["description"] == "https://example.com/feed.xml"
