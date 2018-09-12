#!/usr/bin/env python
from docxtpl import DocxTemplate

data = {
    "case": {
  "customFields": {},
  "owner": "nk",
  "metrics": {},
  "title": "Test all the Things!",
  "flag": False,
  "caseId": 1,
  "status": "Open",
  "startDate": 1522762860000,
  "severity": 1,
  "createdBy": "nk",
  "tlp": 2,
  "description": "![TEST ALL THE THINGS](http://s2.quickmeme.com/img/29/292c2939861f699d5f48f66b096931dc76696f8878e96d08df4f7dd5b4bf6ebd.jpg)",
  "createdAt": 1522762906672,
  "tags": [],
  "updatedBy": "nk",
  "updatedAt": 1522762921669,
  "pap": 2,
  "_type": "case",
  "_routing": "AWKLvf2urD_ITSpJXhlb",
  "_parent": None,
  "_id": "AWKLvf2urD_ITSpJXhlb",
  "_version": 1,
  "id": "AWKLvf2urD_ITSpJXhlb"
    }
}

doc = DocxTemplate('/home/nk/Documents/thp-related/template/case-template.docx')
data['case']['tlp'] = ['TLP:WHITE', 'TLP:GREEN', 'TLP:AMBER', 'TLP:RED'][data['case']['tlp']]
doc.render(data)
doc.save('/tmp/test.docx')