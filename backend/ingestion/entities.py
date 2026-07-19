import re
from typing import Dict, List


class ResumeEntityExtractor:
    TECH_SKILLS = [
        "Python", "JavaScript", "TypeScript", "Java", "C\\+\\+", "C#", "Go", "Rust",
        "React", "Angular", "Vue", "Node\\.?js", "Django", "Flask", "FastAPI",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "Git",
        "SQL", "PostgreSQL", "MongoDB", "Redis", "Kafka", "RabbitMQ",
        "HTML", "CSS", "SASS", "REST", "GraphQL", "gRPC",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
        "Jenkins", "Terraform", "Ansible", "CI/CD",
        "Microservices", "Agile", "Scrum", "JIRA",
        "Figma", "Sketch", "Photoshop",
        "Swift", "Kotlin", "Flutter", "React Native",
        "Bash", "PowerShell", "Perl",
        "Spark", "Hadoop", "Airflow", "dbt",
    ]

    DEGREE_PATTERNS = [
        r"(?:Bachelor(?:'s)?|B\.?S\.?|B\.?A\.?|B\.?E\.?|B\.?Tech)",
        r"(?:Master(?:'s)?|M\.?S\.?|M\.?A\.?|M\.?B\.?A\.?|M\.?Eng)",
        r"(?:Ph\.?D\.?|Doctorate|Doctor(?:'s)?)",
        r"(?:Associate(?:'s)?|A\.?S\.?|A\.?A\.?)",
    ]

    def extract(self, text: str) -> Dict[str, List[str]]:
        return {
            "skills": self._extract_skills(text),
            "projects": self._extract_projects(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "certifications": self._extract_certifications(text),
        }

    def _extract_skills(self, text: str) -> List[str]:
        skills = set()

        pattern = r"(?:skills?|proficient in|technologies|tech stack)[:\s]+([^\n]+)"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            segment = match.group(1)
            capitalized = re.findall(r"\b[A-Z][a-zA-Z#+.]{1,}\b", segment)
            skills.update(capitalized)

        combined = "|".join(self.TECH_SKILLS)
        for match in re.finditer(r"\b(" + combined + r")\b", text, re.IGNORECASE):
            skills.add(match.group(1).strip())

        return sorted(skills)

    def _extract_projects(self, text: str) -> List[str]:
        projects = []

        patterns = [
            r"(?:project|developed|built|created)[:\s]+([^\n]+)",
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                val = match.group(1).strip()
                if len(val) > 10:
                    projects.append(val)

        section_match = re.search(
            r"(?:projects?|portfolio)[:\s]*\n((?:[-•*]\s*.+\n?)+)",
            text, re.IGNORECASE,
        )
        if section_match:
            for line in section_match.group(1).splitlines():
                cleaned = re.sub(r"^[-•*]\s*", "", line).strip()
                if cleaned and cleaned not in projects:
                    projects.append(cleaned)

        return projects

    def _extract_experience(self, text: str) -> List[str]:
        experiences = []

        patterns = [
            r"(\b[\w\s]+(?:Engineer|Developer|Manager|Director|Analyst|Designer|"
            r"Architect|Lead|Head|VP|Chief|Officer|Consultant|Specialist|"
            r"Coordinator|Associate|Intern)\b)\s+(?:at|@)\s+(\w[\w\s&]+)",
            r"(?:worked|employed)\s+(?:at|@)\s+(\w[\w\s&]+)",
            r"(\b[\w\s]+(?:Engineer|Developer|Manager|Director|Analyst|Designer)"
            r"\b)",
        ]

        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                experiences.append(match.group(0).strip())

        return experiences

    def _extract_education(self, text: str) -> List[str]:
        educations = []
        combined_degrees = "|".join(self.DEGREE_PATTERNS)

        for match in re.finditer(
            r"(" + combined_degrees + r")\s+(?:in\s+)?(\w[\w\s,]+)",
            text, re.IGNORECASE,
        ):
            educations.append(match.group(0).strip())

        university_match = re.finditer(
            r"(University of [\w\s]+|[\w\s]+ University|[\w\s]+ Institute (?:of )?Technology)",
            text, re.IGNORECASE,
        )
        for match in university_match:
            edu = match.group(0).strip()
            if edu not in educations:
                educations.append(edu)

        return educations

    def _extract_certifications(self, text: str) -> List[str]:
        certifications = []
        patterns = [
            r"(Certified\s+[\w\s]+(?:Professional|Associate|Specialist|Expert|Engineer)?)",
            r"(AWS Certified\s+[\w\s]+)",
            r"(Google Certified\s+[\w\s]+)",
            r"(Microsoft Certified\s+[\w\s]+)",
            r"(Oracle Certified\s+[\w\s]+)",
            r"(Cisco Certified\s+[\w\s]+)",
            r"(CompTIA\s+[\w\s]+)",
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                cert = match.group(1).strip()
                if cert not in certifications:
                    certifications.append(cert)
        return certifications

    def extract_as_metadata(self, text: str) -> Dict[str, str]:
        entities = self.extract(text)
        metadata = {}
        for key, values in entities.items():
            if values:
                metadata[key] = ", ".join(values)
            else:
                metadata[key] = ""
        return metadata
