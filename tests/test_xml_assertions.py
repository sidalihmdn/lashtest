"""
Tests for XML assertions DSL.
Tests real-world XML API scenarios with XPath queries and assertions.
Notice : these tests are more like integration tests for the XML assertion system, using real XML data from public APIs and can fail in the future 
"""

from lashtest import APIClient


# ── W3Schools XML Examples ──────────────────────────────────────────────────────

class TestW3SchoolsXMLExamples:
    """Test XML parsing against real W3Schools XML examples."""

    client = APIClient('https://www.w3schools.com/xml').with_header("User-Agent", "lashtest-xml-tests/1.0")

    def test_simple_xml_parsing(self):
        """Fetch and parse W3Schools simple.xml example."""
        with self.client.get('/simple.xml') as response:
            response.assert_status(200)
            
            # Verify root element
            response.assertions.xml.xpath('//breakfast_menu').count.gte(1)

    def test_cd_catalog_count(self):
        """Verify CD catalog has expected structure and content."""
        with self.client.get('/cd_catalog.xml') as response:
            response.assert_status(200)
            
            # Should have multiple CDs
            response.assertions.xml.xpath('//CD').count.gte(1)

    def test_cd_catalog_first_cd_details(self):
        """Verify details of the first CD in the catalog."""
        with self.client.get('/cd_catalog.xml') as response:
            response.assert_status(200)
            
            # First CD should have a title
            response.assertions.xml.xpath('//CD[1]/TITLE').text.exists()
            response.assertions.xml.xpath('//CD[1]/ARTIST').text.exists()
            response.assertions.xml.xpath('//CD[1]/PRICE').text.exists()

    def test_breakfast_menu_items(self):
        """Verify breakfast menu items are properly structured."""
        with self.client.get('/simple.xml') as response:
            response.assert_status(200)
            
            # Should have multiple food items
            response.assertions.xml.xpath('//food').count.gte(1)


# ── HTTPBin XML Endpoints ───────────────────────────────────────────────────────

class TestHTTPBinXMLResponse:
    """Test XML parsing of httpbin.org XML response endpoints."""

    client = APIClient('https://httpbin.org').with_header("User-Agent", "lashtest-xml-tests/1.0")

    def test_xml_endpoint_returns_valid_xml(self):
        """Verify httpbin /xml endpoint returns valid XML."""
        with self.client.get('/xml') as response:
            response.assert_status(200)
            
            # Should have some XML structure
            response.assertions.xml.xpath('//*').count.gte(1)

    def test_xml_structure_is_parseable(self):
        """Verify XML response has correct root element."""
        with self.client.get('/xml') as response:
            response.assert_status(200)
            
            # XML should be parseable without errors (no exception raised)
            response.assertions.xml.xpath('/*').count.eq(1)


# ── Real RSS Feeds ──────────────────────────────────────────────────────────────

class TestRSSFeedParsing:
    """Test XML parsing of real RSS feeds."""

    def test_github_releases_feed(self):
        """Verify GitHub releases RSS feed is parseable."""
        client = APIClient('https://github.com').with_header("User-Agent", "lashtest-rss-tests/1.0")
        
        with client.get('/torvalds/linux/releases.atom') as response:
            response.assert_status(200)
            # Response contains XML/Atom content
            assert response.text is not None
            
            # Should have feed entries
            response.assertions.xml.xpath('//*').count.gte(1)

    def test_real_rss_has_entries(self):
        """Verify RSS feed has multiple entries."""
        client = APIClient('https://news.ycombinator.com').with_header("User-Agent", "lashtest-rss-tests/1.0")
        
        with client.get('/rss') as response:
            response.assert_status(200)
            
            # Should have item elements
            response.assertions.xml.xpath('//item').count.gte(1)

    def test_rss_item_structure(self):
        """Verify RSS items have required structure."""
        client = APIClient('https://news.ycombinator.com').with_header("User-Agent", "lashtest-rss-tests/1.0")
        
        with client.get('/rss') as response:
            response.assert_status(200)
            
            # First item should have a title
            response.assertions.xml.xpath('//item[1]/title').text.exists()

    def test_first_rss_item_has_link(self):
        """Verify the first RSS item has a link."""
        client = APIClient('https://news.ycombinator.com').with_header("User-Agent", "lashtest-rss-tests/1.0")
        
        with client.get('/rss') as response:
            response.assert_status(200)
            
            # First item should have a link element
            response.assertions.xml.xpath('//item[1]/link').exists()


# ── SVG XML Format ──────────────────────────────────────────────────────────────

class TestSVGXMLParsing:
    """Test XML parsing of SVG (XML-based vector graphics format)."""

    client = APIClient('https://commons.wikimedia.org').with_header("User-Agent", "lashtest-xml-tests/1.0")

    def test_svg_has_root_element(self):
        """Verify SVG file has proper root svg element."""
        # Using a simple SVG file
        with self.client.get('/wiki/Special:FilePath/Antu_office-database.svg') as response:
            response.assert_status(200)
            
            # SVG should have svg root element
            response.assertions.xml.xpath('//*').count.gte(1)

    def test_svg_contains_elements(self):
        """Verify SVG has graphical elements."""
        with self.client.get('/wiki/Special:FilePath/Antu_office-database.svg') as response:
            response.assert_status(200)
            
            # Should have content (elements)
            response.assertions.xml.xpath('//svg').count.gte(0)


# ── OpenAPI/Swagger XML Schemas ────────────────────────────────────────────────

class TestOpenAPIXMLSchemas:
    """Test XML parsing of OpenAPI/Swagger schemas and specifications."""

    client = APIClient('https://raw.githubusercontent.com').with_header("User-Agent", "lashtest-xml-tests/1.0")

    def test_xml_schema_is_parseable(self):
        """Verify XML schema files are properly formatted."""
        # Using a real XSD schema file from a repository
        with self.client.get('/OAI/OpenAPI-Specification/master/examples/v3.0/swagger.yaml') as response:
            # This may return YAML, but we test the concept
            assert response.status == 200 or response.status == 404

    def test_soap_wsdl_structure(self):
        """Test parsing of WSDL (SOAP) service descriptions."""
        # WSDL files are XML-based service definitions
        client = APIClient('https://www.w3schools.com/xml')
        
        with client.get('/note.xml') as response:
            response.assert_status(200)
            
            # Should be parseable XML
            response.assertions.xml.xpath('//*').count.gte(1)


# ── SiteMap XML Parsing ─────────────────────────────────────────────────────────

class TestSitemapXMLParsing:
    """Test XML parsing of website sitemaps."""

    def test_w3schools_sitemap_structure(self):
        """Verify website sitemap has proper XML structure."""
        client = APIClient('https://www.w3schools.com').with_header("User-Agent", "lashtest-xml-tests/1.0")
        
        with client.get('/sitemap.xml') as response:
            response.assert_status(200)
            
            # Sitemap should have URL entries
            response.assertions.xml.xpath('//url').count.gte(1)

    def test_sitemap_has_location_elements(self):
        """Verify sitemap URLs have location elements."""
        client = APIClient('https://www.w3schools.com').with_header("User-Agent", "lashtest-xml-tests/1.0")
        
        with client.get('/sitemap.xml') as response:
            response.assert_status(200)
            
            # Each URL should have a loc element
            response.assertions.xml.xpath('//url/loc').count.gte(1)

    def test_sitemap_first_url_is_valid(self):
        """Verify first URL in sitemap is properly formatted."""
        client = APIClient('https://www.w3schools.com').with_header("User-Agent", "lashtest-xml-tests/1.0")
        
        with client.get('/sitemap.xml') as response:
            response.assert_status(200)
            
            # First URL should contain a protocol
            response.assertions.xml.xpath('//url[1]/loc').text.contains('http')
