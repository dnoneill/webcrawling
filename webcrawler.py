import requests, os, PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import re, time
from urllib.parse import urljoin
import concurrent.futures
CONNECTIONS = 100
TIMEOUT = 5
missing_urls = ['https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/content/Images_Centennial/Img_008', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/julian.htm', 'https://www.lib.ncsu.edu/gis/docs/Maps_NCGS_OFR_2005_01_fig_1.pdf', 'https://www.lib.ncsu.edu/publications/focus-online/students-walk-in-the-brickyard-II+I', 'https://www.lib.ncsu.edu/databases/1990-long-form-2010-boundaries', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/support.php', 'https://www.lib.ncsu.edu/ncgdap/index.html', 'https://www.lib.ncsu.edu/gis/esridm/2014/help/whatsnew.htm', 'https://www.lib.ncsu.edu/okc/resources/faqs/fairuse', 'https://www.lib.ncsu.edu/scrc/animal-rights-welfare', 'https://www.lib.ncsu.edu/archivedexhibits/sodfather/PDF/grahambrochure2.pdf', 'https://www.lib.ncsu.edu/databases/advanced-technologies-aerospace-database', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.32', 'https://www.lib.ncsu.edu/events/mlk-commemoration-week-pop-exhibit', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/book.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/collaboration.html', 'https://www.lib.ncsu.edu/news/focus/%E2%80%9Ci-had-a-good-sense-of-what-was-coming%E2%80%9D-%E2%80%93--an-interview-with-susan-k-nutter', 'https://www.lib.ncsu.edu/archivedexhibits/women/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/early.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/inspiration.html', 'https://www.lib.ncsu.edu/ncgdap/documents/Morris_LibraryTrends_09.pdf', 'https://www.lib.ncsu.edu/news/special-collections/special-collections-works-with-dr-james-mulhollands-eng-260-students', 'https://www.lib.ncsu.edu/case-statement/graduates.php', 'https://www.lib.ncsu.edu/endowments/armstrong-endowment', 'https://www.lib.ncsu.edu/archivedexhibits/patents/textiles.htm', 'https://www.lib.ncsu.edu/endowments/edmund-winslow-and-dorothy-hilmer-nutter-endowment', 'https://www.lib.ncsu.edu/news/student-artists-win-code%2Bart-prizes', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/charrette_response.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/introduction.htm', 'https://www.lib.ncsu.edu/events/femme-game-night-2', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8b.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/desc1.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/interpretation.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tfarm.html', 'https://www.lib.ncsu.edu/staff/notfound', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Pams.htm', 'https://www.lib.ncsu.edu/news/makeathon-teams-take-on-sustainability-challenges-at-ncsu-libraries', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/index.php', 'https://www.lib.ncsu.edu/news/libraries-partners-with-aspca-on-largescale-digitization-of-animal-welfare-materials', 'https://www.lib.ncsu.edu/findingaids/mc00518', 'https://www.lib.ncsu.edu/findingaids/mc00205', 'https://www.lib.ncsu.edu/news/technology-with-a-mad-beat', 'https://www.lib.ncsu.edu/findingaids/mc00003', 'https://www.lib.ncsu.edu/findingaids/mc00401', 'https://www.lib.ncsu.edu/gis/esridm/2006/help/aboutedm.htm', 'https://www.lib.ncsu.edu/archivedexhibits/women/2000.htm', 'https://www.lib.ncsu.edu/events/global-film-series-rafiki', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings8.htm', 'https://www.lib.ncsu.edu/news/veterinary-medicine/new-materials-nov-6', 'https://www.lib.ncsu.edu/news/special-collections/dr-matthew-bookers-suburban-history-class-meets-with-special-collections', 'https://www.lib.ncsu.edu/archivedexhibits/wells/index.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.31', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/about.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/credits.html', 'https://www.lib.ncsu.edu/endowments/louis-and-margaret-dowdy-endowment', 'https://www.lib.ncsu.edu/electronic-resource-trials', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/events.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/text2.html', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/life.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/charrette.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/faculty.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/matshouse.htm', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.26', 'https://www.lib.ncsu.edu/spaces/faculty-focus-5210', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/integration.html', 'https://www.lib.ncsu.edu/endowments/joseph-and-robin-hightower-endowment', 'https://www.lib.ncsu.edu/ncgdap/research.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/albert_lambert.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/help.html', 'https://www.lib.ncsu.edu/news/ncsu-libraries-demos-virtual-reality-gear-for-lending', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/creation.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse4.html', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace', 'https://www.lib.ncsu.edu/citation-management/zotero/zoteroword', 'https://www.lib.ncsu.edu/news/special-collections/special-collections-holds-landscape-architecture-class-session-for-dr-magallanes-students', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/recent.html', 'https://www.lib.ncsu.edu/news/join-us-for-maker-days-august-2427', 'https://www.lib.ncsu.edu/projects/department/Acquisitions-%26-Discovery', 'https://www.lib.ncsu.edu/news/special-collections/special-collections-partners-with-cod-faculty-member-kofi-boone-to-evaluate-lost-landscapes-on-campus', 'https://www.lib.ncsu.edu/news/main-news/remembering-susan-k-nutter', 'https://www.lib.ncsu.edu/okc/copyright/instruction/context', 'https://www.lib.ncsu.edu/archivedexhibits/women/1970.htm', 'https://www.lib.ncsu.edu/ncgdap/presentations/Jan_06_Partners_Meeting_poster.pdf', 'https://www.lib.ncsu.edu/gis/docs/OFR2005-1.pdf', 'https://www.lib.ncsu.edu/news/3dprinted-ceramics-combine-tradition-with-technology', 'https://www.lib.ncsu.edu/archivedexhibits/pulitzer/home.html', 'https://www.lib.ncsu.edu/do/open-research/scholarly-sharing', 'https://www.lib.ncsu.edu/news/the-libraries-spotlight-their-best-student-assistants', 'https://www.lib.ncsu.edu/user-studies', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings3.htm', 'https://www.lib.ncsu.edu/gis/esridm/2014/help/aboutedm.htm', 'https://www.lib.ncsu.edu/archivedexhibits/patents/forestry.htm', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/huntlibrary.php', 'https://www.lib.ncsu.edu/archivedexhibits/sodfather/PDF/grahambrochure1.pdf', 'https://www.lib.ncsu.edu/news/makeathon-nets-another-sustainability-fund-grant', 'https://www.lib.ncsu.edu/archivedexhibits/women/1960.htm', 'https://www.lib.ncsu.edu/endowments/frank-and-eleanor-hart-endowment', 'https://www.lib.ncsu.edu/repository/spr/sprguidelines/SPR+Guidelines+Final+03-08', 'https://www.lib.ncsu.edu/ncgdap/presentations.html', 'https://www.lib.ncsu.edu/toward-a-better-planet-symposium/support', 'https://www.lib.ncsu.edu/archivedexhibits/women/1890.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tculture.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4b.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/about.html', 'https://www.lib.ncsu.edu/news/ncsu-libraries-taps-20082010-fellows', 'https://www.lib.ncsu.edu/news/the-nubian-message-goes-digital', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/scijo.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/dedication.php', 'https://www.lib.ncsu.edu/endowments/cooper-library-endowment', 'https://www.lib.ncsu.edu/news/the-makerspace-team', 'https://www.lib.ncsu.edu/faculty-award', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/intro.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/early.html', 'https://www.lib.ncsu.edu/ncgdap/presentations/GITA2006poster.pdf', 'https://www.lib.ncsu.edu/events/stress-busters-drop-space-3', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.27', 'https://www.lib.ncsu.edu/news/the-iot-internetconnected-toys-and-your-datarich-future', 'https://www.lib.ncsu.edu/news/ncsu-libraries-fellows-20102012', 'https://www.lib.ncsu.edu/databases/aata-online', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/pbcl/profile.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/darwin.htm', 'https://www.lib.ncsu.edu/do/data-management/what-is-a-dmp', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.29', 'https://www.lib.ncsu.edu/archivedexhibits/smith/bibliography.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/pbcl/sustainability.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1990.htm', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/library.html', 'https://www.lib.ncsu.edu/news/pentair-foundation-supports-stem-programing-instruction-at-the-ncsu-libraries', 'https://www.lib.ncsu.edu/gis/counties/county_map.html', 'https://www.lib.ncsu.edu/archivedexhibits/smith/awards.html', 'https://www.lib.ncsu.edu/findingaids/mc00535', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/voyages.html', 'https://www.lib.ncsu.edu/archivedexhibits/sports/trappings.html', 'https://www.lib.ncsu.edu/ncgdap/presentations/GISDay2005poster.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/sld002.htm', 'https://www.lib.ncsu.edu/gis/esridm/2006/help/sm_overview.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/credits.html', 'https://www.lib.ncsu.edu/events/3d-printing-ceramics-professor-taekyeom-lee', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/biography.htm', 'https://www.lib.ncsu.edu/findingaids/ua016_001', 'https://www.lib.ncsu.edu/findingaids/mss00402', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/timeline-lib.php', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit5.html', 'https://www.lib.ncsu.edu/ncgdap/contact.html', 'https://www.lib.ncsu.edu/gis/counties/mecklenb.html', 'https://www.lib.ncsu.edu/case-statement/faculty.php', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings7.htm', 'https://www.lib.ncsu.edu/tripsaver/document-delivery-FOL', 'https://www.lib.ncsu.edu/archivedexhibits/patents/CALS.htm', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings1.htm', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/creativity.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.33', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/degw.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/thomas_leake.php', 'https://www.lib.ncsu.edu/archivedexhibits/hats/index.html', 'https://www.lib.ncsu.edu/news/%E2%80%9Cthe-dynamic-sun%E2%80%9D-combines-solar-physics-and-visualization', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/pbcl/design.html', 'https://www.lib.ncsu.edu/news/alumni-lead-private-support-of-ncsu-libraries%E2%80%99-makerspace', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/parking.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1950.htm', 'https://www.lib.ncsu.edu/instruction/writing-speaking', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Engineering.htm', 'https://www.lib.ncsu.edu/spaces/hill-library-makerspace/policies', 'https://www.lib.ncsu.edu/gis/esridm/2006/help/sm_about_data.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/learn.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1940.htm', 'https://www.lib.ncsu.edu/archivedexhibits/sports/battlefield.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1920.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/histories.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3c.html', 'https://www.lib.ncsu.edu/databases/accounting-tax-banking-collection', 'https://www.lib.ncsu.edu/events/stress-buster-come-make-slime', 'https://www.lib.ncsu.edu/databases/agecon-search', 'https://www.lib.ncsu.edu/spaces/faculty-workroom-2312b', 'https://www.lib.ncsu.edu/citation-management/zotero/gsimport', 'https://www.lib.ncsu.edu/archivedexhibits/sports/boom.html', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/prelinn.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/ebhenderson.php', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/tipp.html', 'https://www.lib.ncsu.edu/databases/1980-census-2010-boundaries', 'https://www.lib.ncsu.edu/events/femme-making-night-makerspace-0', 'https://www.lib.ncsu.edu/events/swimming-sharks-day-1', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.35', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/peter_ihrie.php', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/access.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit6.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/index.html', 'https://www.lib.ncsu.edu/formats/teaching-and-learning-datasets', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings9.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2a.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/process.html', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/college.html', 'https://www.lib.ncsu.edu/stories/threading-needle-fostering-student-success-through-making', 'https://www.lib.ncsu.edu/endowments/arnold-addison-and-mildred-barner-endowment', 'https://www.lib.ncsu.edu/archivedexhibits/pams/index.php', 'https://www.lib.ncsu.edu/databases/2000-long-form-2010-boundaries', 'https://www.lib.ncsu.edu/events/robotics-gateway-coding-and-creativity', 'https://www.lib.ncsu.edu/stories/dont-throw-away-assignment-students-improve-wikipedia-through-wikiedu', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tentom.html', 'https://www.lib.ncsu.edu/case-statement/community.php', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.25', 'https://www.lib.ncsu.edu/events/jazsalyn-mcneil-creator-pulse-dress', 'https://www.lib.ncsu.edu/events/de-stress-fest-inking-some-manga', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8a.html', 'https://www.lib.ncsu.edu/news/makeathon-exceeds-all-expectations', 'https://www.lib.ncsu.edu/spaces/faculty-workroom-2312a', 'https://www.lib.ncsu.edu/events/making-space-cotton-candy-conversation-jackie-morin', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/index.html', 'https://www.lib.ncsu.edu/ncgdap/documents/ndiipp-proposal.doc', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/timeline.html', 'https://www.lib.ncsu.edu/stories/coyote-who-said-cheese-and-wolfpack-citizen-science-challenge', 'https://www.lib.ncsu.edu/news/ncsu-libraries-fellows-20112013', 'https://www.lib.ncsu.edu/news/ncsu-libraries-receives-lsta-grant-to-continue-digitization-of-agricultural-documents', 'https://www.lib.ncsu.edu/news/ncsu-libraries-announces-libraries-fellows-class', 'https://www.lib.ncsu.edu/databases/abc-clio-ebook-collection', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/index.html', 'https://www.lib.ncsu.edu/databases/aa-eportal', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/text.html', 'https://www.lib.ncsu.edu/events/future-wearables-0', 'https://www.lib.ncsu.edu/news/staff-news/makeathon-wins-a-sustainability-fund-grant', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/timeline.php', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/foxquiz.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings2.htm', 'https://www.lib.ncsu.edu/projects/department/Collections-%26-Research-Strategy', 'https://www.lib.ncsu.edu/news/victoria-rind-and-her-amazing-wearables', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/wallace_riddick.php', 'https://www.lib.ncsu.edu/archivedexhibits/sports/hoops.html', 'https://www.lib.ncsu.edu/ncgdap/presentations/NCGIS2005_Poster_v1.6.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/pbcl/connections.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8c.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7b.html', 'https://www.lib.ncsu.edu/scrc/lewisclarke/bibliography-chronological', 'https://www.lib.ncsu.edu/findingaids/mss00399', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/intro.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings4.htm', 'https://www.lib.ncsu.edu/archivedexhibits/sports/credits.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/credits.html', 'https://www.lib.ncsu.edu/archivedexhibits/smith/writer.html', 'https://www.lib.ncsu.edu/ncgdap/publications.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.30', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/bibliography.php', 'https://www.lib.ncsu.edu/citation-management/zotero/zoteroimport', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/victorian.html', 'https://www.lib.ncsu.edu/endowments/carl-evelyn-koch-endowment', 'https://www.lib.ncsu.edu/databases/sage-data-formerly-data-planet', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/landscape.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.23', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/pressphotos.htm', 'https://www.lib.ncsu.edu/gis/docs/lulc87.htm', 'https://www.lib.ncsu.edu/news/garrett-and-hill-join-20122014-library-fellows', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.24', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse3.html', 'https://www.lib.ncsu.edu/projects/department/Learning-Spaces-%26-Services', 'https://www.lib.ncsu.edu/services/makerspace/instructors', 'https://www.lib.ncsu.edu/gis/esridm/2006/help/sm_converting.htm', 'https://www.lib.ncsu.edu/citationbuilder/assets/plus-square-solid.svg', 'https://www.lib.ncsu.edu/protected-areas-gis', 'https://www.lib.ncsu.edu/endowments/leonard-and-eleanor-aurand-endowment', 'https://www.lib.ncsu.edu/citationbuilder/assets/minus-square-solid.svg', 'https://www.lib.ncsu.edu/endowments/roberta-r-havner-endowment', 'https://www.lib.ncsu.edu/shout-outs/single/84671', 'https://www.lib.ncsu.edu/hill/visit/directions', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/visiting.html', 'https://www.lib.ncsu.edu/news/2017-code%2Bart-student-contest-winners-announced', 'https://www.lib.ncsu.edu/experiencing-king/researchers.php', 'https://www.lib.ncsu.edu/hunt-library/naming-opportunities', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadmodel.htm', 'https://www.lib.ncsu.edu/news/special-collections/student-spotlight-ellie-beal-special-collections-desk-assistant', 'https://www.lib.ncsu.edu/stories/women-stem-build-community-and-circuits-e-textiles-workshop', 'https://www.lib.ncsu.edu/tripsaver/document-delivery', 'https://www.lib.ncsu.edu/archivedexhibits/smith/career.html', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/lattylet.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/desc2.html', 'https://www.lib.ncsu.edu/ncgdap/documents/archiving2006.pdf', 'https://www.lib.ncsu.edu/ncgdap/presentations/NCGeologicSurvey_DMT2006_posterA.PDF', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit8.html', 'https://www.lib.ncsu.edu/stories/modeling-continental-erosion-and-mountaintop-mining-library', 'https://www.lib.ncsu.edu/legacy-mlk-nc-state/share-your-story', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/centennial.php', 'https://www.lib.ncsu.edu/archivedexhibits/sports/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/thistory.html', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/resources.php', 'https://www.lib.ncsu.edu/events/user-experience-in-video-game-design-with-dr-celia-hodent-epic-games', 'https://www.lib.ncsu.edu/ncgdap/partners.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit.html', 'https://www.lib.ncsu.edu/archivedexhibits/smith/images/adlai%20stevenson%20story.pdf', 'https://www.lib.ncsu.edu/events/stress-busters-drop-space-2', 'https://www.lib.ncsu.edu/databases/advertising-america', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/matsbio.htm', 'https://www.lib.ncsu.edu/archivedexhibits/women/1930.htm', 'https://www.lib.ncsu.edu/news/staff-news/congratulations-to-our-very-own-susan-k-nutter%E2%80%942016-acrl-librarian-of-the-year', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/philosophy.html', 'https://www.lib.ncsu.edu/news/staff-news/welcome-20162018-ncsu-libraries-fellows', 'https://www.lib.ncsu.edu/archivedexhibits/patents/Design.htm', 'https://www.lib.ncsu.edu/exhibits/art-augmented-reality-3d', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse2.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/index.html', 'https://www.lib.ncsu.edu/databases/afghanistan-making-us-policy-1973-1990', 'https://www.lib.ncsu.edu/news/the-library-of-the-future-gets-an-unexpected-closeup', 'https://www.lib.ncsu.edu/archivedexhibits/sports/changes.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1980.htm', 'https://www.lib.ncsu.edu/hunt', 'https://www.lib.ncsu.edu/digital-collections', 'https://www.lib.ncsu.edu/news/do-you-know-your-animals%3F', 'https://www.lib.ncsu.edu/ncgdap/presentations/NCGeologicSurvey_DMT2006_posterB.PDF', 'https://www.lib.ncsu.edu/instruction/writing-speaking/faq', 'https://www.lib.ncsu.edu/events/postponed-global-film-series-grazing-amazon', 'https://www.lib.ncsu.edu/tripsaver-interlibrary-loan-faq', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/mastawds.htm', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3b.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings6.htm', 'https://www.lib.ncsu.edu/archivedexhibits/sports/gridiron.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/browse.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/collections.html', 'https://www.lib.ncsu.edu/citation-management/zotero/zoterolookup', 'https://www.lib.ncsu.edu/ncgdap/documents/MorrisLibraryTrendsFall2006.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/smith/index.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.34', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit2b.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/about.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/VetMed.htm', 'https://www.lib.ncsu.edu/news/two-ncsu-librarians-receive-gertrude-cox-award-for-innovative-excellence-in-teaching-and-learning-with-technology', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7.html', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/linneaus.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/drawings5.htm', 'https://www.lib.ncsu.edu/newspaperbytitle', 'https://www.lib.ncsu.edu/archivedexhibits/sodfather/PDF/sodfather.pdf', 'https://www.lib.ncsu.edu/databases/all', 'https://www.lib.ncsu.edu/endowments/frank-and-judy-abrams-endowment', 'https://www.lib.ncsu.edu/archivedexhibits/maryeannefox/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4a.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/sld003.htm', 'https://www.lib.ncsu.edu/userstudies/studies/2010GISfocusgroup', 'https://www.lib.ncsu.edu/archivedexhibits/textiles/anniversary/nelsonhall.php', 'https://www.lib.ncsu.edu/events/crafting-resilience-drop-space-6', 'https://www.lib.ncsu.edu/projects/department/Data-%26-Visualization-Services', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit4c.html', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/young.html', 'https://www.lib.ncsu.edu/ncgdap/documents/NCGDAP_InterimReport_June2008.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit7a.html', 'https://www.lib.ncsu.edu/archivedexhibits/patents/PDF/bennett.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tecon.html', 'https://www.lib.ncsu.edu/archivedexhibits/wells/nomenclature.html', 'https://www.lib.ncsu.edu/archivedexhibits/westwood/westwoodwork.htm', 'https://www.lib.ncsu.edu/multisearch-think-aloud-usability-study-2004-user-studies', 'https://www.lib.ncsu.edu/spaces/faculty-workroom-5232', 'https://www.lib.ncsu.edu/events/future-wearables', 'https://www.lib.ncsu.edu/news/special-collections/recipes-from-world-war-i-%28part-3%29--sweetless-%28sugarless%29', 'https://www.lib.ncsu.edu/archivedexhibits/requiem/home.html', 'https://www.lib.ncsu.edu/archivedexhibits/women/1901.htm', 'https://www.lib.ncsu.edu/archivedexhibits/tippmann/index.html', 'https://www.lib.ncsu.edu/archivedexhibits/tobacco/tliterature.html', 'https://www.lib.ncsu.edu/gis/lidar/Bob_Ryan_Earthdata.pps', 'https://www.lib.ncsu.edu/gis/esridm/2014/help/rdstrght.htm', 'https://www.lib.ncsu.edu/facilities-and-tech-overview', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadover.htm', 'https://www.lib.ncsu.edu/archivedexhibits/patents/PDF/foodexpo.pdf', 'https://www.lib.ncsu.edu/ncgdap/links.html', 'https://www.lib.ncsu.edu/publications/NLarchives/NL.vol.36', 'https://www.lib.ncsu.edu/findingaids/mss00401', 'https://www.lib.ncsu.edu/okc/resources/faqs/classroom', 'https://www.lib.ncsu.edu/case-statement/students.php', 'https://www.lib.ncsu.edu/citation-management/zotero/ebscoimport', 'https://www.lib.ncsu.edu/ncgdap/presentations/PartnersMeeting705poster.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/matsumoto/gadwall.htm', 'https://www.lib.ncsu.edu/okc/membershipcriteria', 'https://www.lib.ncsu.edu/gis/docs/2016_JE_HistoricAerialPhotos.pdf', 'https://www.lib.ncsu.edu/archivedexhibits/wells/exhibit3a.html', 'https://www.lib.ncsu.edu/archivedexhibits/hunt/teamwork.html', 'https://www.lib.ncsu.edu/stories/codeart-different-kind-data-experience', 'https://www.lib.ncsu.edu/ncgdap/documents.html']

urls = open("seed.txt").read().strip().split("\n")
print(urls)
#urls = ['https://www.lib.ncsu.edu/events/']
filters = open("regex-urlfilter.txt").read().strip().split("\n")
filters = list(filter(lambda x: x.startswith('#') == False and x, filters))
negativefilters = list(filter(lambda x: x.startswith('-'), filters))
negativefilters = "|".join(list(map(lambda x: x.strip('-'),negativefilters)))
positivefilters = list(filter(lambda x: x.startswith('+'), filters))
positivefilters = "|".join(list(map(lambda x: x.strip('+'),positivefilters)))
all_data = {}
process_urls = []
processed_urls = []
retry_urls = []
import requests

def checkUrl(url):
	#negpattern = re.compile(r'{}'.format(negativefilters))
	negmatch = re.search(r'{}'.format(negativefilters), url)
	positivematch = re.search(r'{}'.format(positivefilters), url)
	if positivematch and negmatch == None:
		return True
	else:
		#print(url)
		return False

#print(;fa;dlskfa;lsdkfl;af)
def getContents(url):
	# print('get contents')
	#print(url)
	# print(checkUrl(url))
	try:
		response = requests.get(url)
		#print(response.status_code)
		parseContents(response, url)
	except Exception as e:
		print(e)
		retry_urls.append(url)
		process_urls.remove(url)
		print('problem url {}$$$$$$$'.format(url))
	return 'FALJDFLDAKJFADSLKJFALKDJFALKSJFLKASDJFALSKDJFALKSDJ'
	

def parseContents(response, original_url):
	content = ''
	page_urls = None
	title = original_url
	schemamarkup = {}
	if original_url.lower().endswith('.pdf') and response.status_code < 400:
		with BytesIO(response.content) as data:
			read_pdf = PyPDF2.PdfReader(data)
			for page in range(len(read_pdf.pages)):
				content += read_pdf.pages[page].extract_text()
	elif (original_url.lower().endswith('.doc') or original_url.lower().endswith('.docx')) and response.status_code < 400:
		content = BytesIO(response.content).read()
	else:
		parsed_html = BeautifulSoup(response.content, "html.parser" )
		content = parsed_html.body.get_text() if parsed_html.body else 'find me no text'
		title = parsed_html.title.get_text() if parsed_html.title else original_url
		page_urls = parsed_html.find_all('a', href=True)
		original_url = original_url.rstrip('/')
		schemamarkup = parsed_html.find("script", {"type": "application/ld+json"})
		for index, url in enumerate(page_urls):
			clean_url = url['href'].rsplit("/#", 1)[0].strip()
			if 'node' in clean_url and 'http' not in clean_url:
				origin_url = original_url.replace('https://', '').split('/')[0]
				clean_url = urljoin("https://{}".format(origin_url), clean_url)
			elif 'http' not in clean_url and re.match(r'{}'.format(negativefilters), clean_url) == False:
				clean_url = urljoin(original_url, clean_url)
			clean_url = clean_url.rstrip('/').strip()
			if clean_url in missing_urls:
				print(clean_url)
			#print(checkUrl(clean_url) and clean_url not in process_urls and clean_url not in all_data.keys() and any(url in clean_url for url in urls))
			if checkUrl(clean_url) and clean_url not in process_urls and clean_url not in processed_urls:
				process_urls.append(clean_url)
			if clean_url in process_urls and clean_url in missing_urls:
				print('its in there')
	all_data[original_url] = {'content': content, 'title': title, 'urls_on_page': page_urls,
		'schemamarkup': schemamarkup, 'status_code': response.status_code
	}
	processed_urls.append(original_url)
	processed_urls.append(response.url)
	try:
		process_urls.remove(original_url)
	except Exception as e:
		print(e)

for url in urls:
	getContents(url)

while len(process_urls) > 0:
	with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
		# print([url for url in process_urls[0:CONNECTIONS]])
		# print('100 urls')
		future_to_url = (executor.submit(getContents(url), url, TIMEOUT) for url in process_urls[0:CONNECTIONS])
		time1 = time.time()
		for future in concurrent.futures.as_completed(future_to_url):
			#print('all_data {}'.format(len(all_data.keys())))
			pass
			#print('process_urls {}'.format(len(process_urls)))
	time2 = time.time()
	# process_urls = list(set(process_urls))
	# print(len(process_urls))
	# if process_urls[0] not in processed_urls:
	# 	getContents(process_urls[0])
	# else:
	# 	print('else statement')
	# 	process_urls.remove(process_urls[0])
print(list(all_data.keys()))
print(len(all_data.keys()))
