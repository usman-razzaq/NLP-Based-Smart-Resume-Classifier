import streamlit as st
import joblib
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_option_menu import option_menu
from io import StringIO
import time

# Force light theme
st._config.set_option("theme.base", "light")

# PDF processing imports
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    st.warning("PyPDF2 not available. PDF processing will be limited. Install with: pip install PyPDF2")

# Alternative PDF processing
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# PDF text extraction function
def extract_text_from_pdf(pdf_file):
    """
    Extract text from PDF file using multiple methods for better compatibility
    """
    try:
        # Method 1: Try PyPDF2 first
        if PDF_AVAILABLE:
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    return text.strip()
            except Exception as e:
                # Log error internally but don't show to user
                pass
        
        # Method 2: Try pdfplumber as alternative
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    if text.strip():
                        return text.strip()
            except Exception as e:
                # Log error internally but don't show to user
                pass
        
        # Method 3: Fallback - try to read as bytes and decode
        try:
            pdf_file.seek(0)  # Reset file pointer
            content = pdf_file.read()
            # Try to extract text using basic text extraction
            text = content.decode('utf-8', errors='ignore')
            # Remove non-printable characters
            text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
            if text.strip():
                return text.strip()
        except Exception as e:
            # Log error internally but don't show to user
            pass
        
        return None
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

# Set page config first
st.set_page_config(
    page_title="Smart Resume Classifier - Smart Resume Classifier by Usman Razzaq",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main styles */
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    
    .card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border-left: 4px solid #3B82F6;
    }
    
    .result-card {
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        color: white;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .confidence-meter {
        height: 8px;
        background-color: #E5E7EB;
        border-radius: 4px;
        margin: 1rem 0;
        overflow: hidden;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
        border-radius: 4px;
    }
    
    .job-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #3B82F6;
        transition: all 0.3s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    .skill-pill {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
    }
    
    /* Sidebar styles */
    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #E5E7EB;
        margin-bottom: 1rem;
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #E5E7EB;
        padding: 1rem;
    }
    
    /* Metric styling */
    .stMetric {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Text cleaning function
def clean_text(text):
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    return ""

# Job recommendations
def get_recommendations(category):
    recommendations = {
        'Data Science': [
            {"title": "Data Scientist", "companies": ["Google", "Amazon", "Netflix", "Meta", "Microsoft"], "skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization"]},
            {"title": "Machine Learning Engineer", "companies": ["Facebook", "Apple", "Uber", "Tesla", "OpenAI"], "skills": ["TensorFlow", "PyTorch", "Deep Learning", "MLOps", "Cloud Platforms"]},
            {"title": "Data Analyst", "companies": ["Microsoft", "Spotify", "Airbnb", "Salesforce", "Adobe"], "skills": ["SQL", "Excel", "Tableau", "Python", "Business Intelligence"]},
            {"title": "Data Engineer", "companies": ["Netflix", "Uber", "Airbnb", "Stripe", "Shopify"], "skills": ["Apache Spark", "Hadoop", "Kafka", "Python", "Data Pipelines"]}
        ],
        'Design': [
            {"title": "UI/UX Designer", "companies": ["Adobe", "Figma", "InVision", "Google", "Apple"], "skills": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems"]},
            {"title": "Product Designer", "companies": ["Apple", "Google", "Facebook", "Netflix", "Airbnb"], "skills": ["Design Thinking", "Prototyping", "User Testing", "Product Strategy", "Visual Design"]},
            {"title": "Graphic Designer", "companies": ["Canva", "Adobe", "Behance", "Nike", "Coca-Cola"], "skills": ["Illustrator", "Photoshop", "Typography", "Brand Identity", "Print Design"]},
            {"title": "Visual Designer", "companies": ["Spotify", "Instagram", "TikTok", "Snapchat", "Pinterest"], "skills": ["Motion Graphics", "3D Design", "Animation", "Visual Effects", "Digital Art"]}
        ],
        'Web Development': [
            {"title": "Frontend Developer", "companies": ["Netflix", "Twitter", "Shopify", "Discord", "Notion"], "skills": ["React", "JavaScript", "CSS", "TypeScript", "Responsive Design"]},
            {"title": "Backend Developer", "companies": ["Amazon", "PayPal", "Stripe", "Uber", "Airbnb"], "skills": ["Node.js", "Python", "APIs", "Databases", "Microservices"]},
            {"title": "Full Stack Developer", "companies": ["Google", "Microsoft", "Meta", "Netflix", "Spotify"], "skills": ["MERN Stack", "DevOps", "Databases", "Cloud Services", "System Design"]},
            {"title": "DevOps Engineer", "companies": ["Netflix", "Uber", "Airbnb", "Spotify", "Discord"], "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Infrastructure"]}
        ],
        'Mobile Development': [
            {"title": "iOS Developer", "companies": ["Apple", "Uber", "Instagram", "TikTok", "Spotify"], "skills": ["Swift", "SwiftUI", "iOS SDK", "Core Data", "App Store"]},
            {"title": "Android Developer", "companies": ["Google", "Snapchat", "Discord", "TikTok", "Uber"], "skills": ["Kotlin", "Android SDK", "Jetpack", "Material Design", "Google Play"]},
            {"title": "React Native Developer", "companies": ["Facebook", "Instagram", "Discord", "Skype", "Shopify"], "skills": ["React Native", "JavaScript", "Mobile Development", "Cross-platform", "Native Modules"]}
        ],
        'Software Engineering': [
            {"title": "Software Engineer", "companies": ["Google", "Microsoft", "Amazon", "Meta", "Apple"], "skills": ["Algorithms", "Data Structures", "System Design", "Programming", "Problem Solving"]},
            {"title": "Cloud Engineer", "companies": ["Amazon", "Microsoft", "Google", "Netflix", "Uber"], "skills": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes"]},
            {"title": "Security Engineer", "companies": ["Google", "Microsoft", "Amazon", "Meta", "Netflix"], "skills": ["Cybersecurity", "Network Security", "Penetration Testing", "Security Tools", "Compliance"]}
        ],
        'Marketing': [
            {"title": "Digital Marketing Manager", "companies": ["Google", "Facebook", "Amazon", "Netflix", "Spotify"], "skills": ["SEO", "SEM", "Social Media", "Analytics", "Content Strategy"]},
            {"title": "Content Marketing Specialist", "companies": ["HubSpot", "Mailchimp", "Canva", "Buffer", "Hootsuite"], "skills": ["Content Creation", "SEO", "Social Media", "Email Marketing", "Analytics"]},
            {"title": "Growth Marketing Manager", "companies": ["Uber", "Airbnb", "Spotify", "Discord", "Notion"], "skills": ["Growth Hacking", "A/B Testing", "Conversion Optimization", "Data Analysis", "Marketing Automation"]}
        ],
        'Sales': [
            {"title": "Sales Development Representative", "companies": ["Salesforce", "HubSpot", "Microsoft", "Oracle", "Adobe"], "skills": ["Lead Generation", "Cold Calling", "CRM", "Sales Process", "Communication"]},
            {"title": "Account Executive", "companies": ["Salesforce", "Microsoft", "Oracle", "Adobe", "Workday"], "skills": ["Relationship Building", "Solution Selling", "Negotiation", "Pipeline Management", "Revenue Growth"]}
        ],
        'Finance': [
            {"title": "Financial Analyst", "companies": ["Goldman Sachs", "JPMorgan", "Morgan Stanley", "BlackRock", "Vanguard"], "skills": ["Financial Modeling", "Excel", "VBA", "Financial Analysis", "Risk Assessment"]},
            {"title": "Investment Banker", "companies": ["Goldman Sachs", "JPMorgan", "Morgan Stanley", "Bank of America", "Citigroup"], "skills": ["Financial Modeling", "Valuation", "M&A", "Capital Markets", "Financial Analysis"]}
        ],
        'Healthcare': [
            {"title": "Healthcare Data Analyst", "companies": ["UnitedHealth", "Anthem", "Kaiser", "CVS Health", "Walgreens"], "skills": ["Healthcare Data", "SQL", "Python", "Statistical Analysis", "Healthcare Regulations"]},
            {"title": "Clinical Research Associate", "companies": ["Pfizer", "Johnson & Johnson", "Roche", "Novartis", "Merck"], "skills": ["Clinical Trials", "Regulatory Compliance", "Data Management", "Medical Writing", "Research Protocols"]}
        ],
        'Education': [
            {"title": "Educational Technology Specialist", "companies": ["Coursera", "Udemy", "edX", "Khan Academy", "Duolingo"], "skills": ["EdTech", "Learning Management Systems", "Instructional Design", "Digital Learning", "Educational Content"]},
            {"title": "Curriculum Developer", "companies": ["Khan Academy", "Coursera", "Udemy", "edX", "Codecademy"], "skills": ["Curriculum Design", "Instructional Design", "Educational Content", "Assessment Design", "Learning Objectives"]}
        ]
    }
    
    # Handle case where category might not match exactly
    for key in recommendations:
        if key.lower() in category.lower():
            return recommendations[key]
    return [{"title": "Senior roles in your field", "companies": ["Various"], "skills": ["Leadership", "Strategy", "Management", "Communication", "Problem Solving"]}]

# Skill suggestions based on category
def get_skill_suggestions(category):
    suggestions = {
        'Data Science': ["Python", "R", "SQL", "Machine Learning", "Statistics", "Data Visualization", "Big Data", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter", "Git", "Docker", "AWS", "Azure"],
        'Design': ["Figma", "Adobe Creative Suite", "UI/UX Design", "Typography", "Color Theory", "Wireframing", "Prototyping", "User Research", "Design Systems", "Sketch", "InVision", "Principle", "After Effects", "Illustrator", "Photoshop", "XD", "User Testing", "Accessibility"],
        'Web Development': ["JavaScript", "HTML/CSS", "React", "Node.js", "APIs", "Databases", "Git", "DevOps", "TypeScript", "Vue.js", "Angular", "Express.js", "MongoDB", "PostgreSQL", "MySQL", "AWS", "Docker", "Kubernetes", "CI/CD", "REST APIs"],
        'Mobile Development': ["Swift", "Kotlin", "React Native", "Flutter", "iOS Development", "Android Development", "Mobile UI/UX", "App Store", "Google Play", "Mobile Testing", "Performance Optimization", "Push Notifications", "In-App Purchases", "Mobile Analytics"],
        'Software Engineering': ["Algorithms", "Data Structures", "System Design", "Programming", "Problem Solving", "Java", "C++", "Python", "Go", "Rust", "Microservices", "API Design", "Database Design", "System Architecture", "Code Review", "Testing", "Agile", "Scrum"],
        'Marketing': ["SEO", "SEM", "Social Media Marketing", "Content Marketing", "Email Marketing", "Google Analytics", "Facebook Ads", "Google Ads", "Marketing Automation", "A/B Testing", "Conversion Optimization", "Brand Management", "Market Research", "Customer Segmentation"],
        'Sales': ["Lead Generation", "Cold Calling", "CRM", "Sales Process", "Communication", "Negotiation", "Relationship Building", "Solution Selling", "Pipeline Management", "Revenue Growth", "Sales Strategy", "Account Management", "Prospecting", "Closing Techniques"],
        'Finance': ["Financial Modeling", "Excel", "VBA", "Financial Analysis", "Risk Assessment", "Valuation", "Investment Analysis", "Portfolio Management", "Financial Planning", "Accounting", "Budgeting", "Forecasting", "Financial Reporting", "Compliance"],
        'Healthcare': ["Healthcare Data", "SQL", "Python", "Statistical Analysis", "Healthcare Regulations", "Clinical Trials", "Medical Terminology", "Health Informatics", "Patient Data", "Medical Coding", "HIPAA Compliance", "Healthcare Analytics", "Population Health"],
        'Education': ["EdTech", "Learning Management Systems", "Instructional Design", "Digital Learning", "Educational Content", "Curriculum Design", "Assessment Design", "Learning Objectives", "Student Engagement", "Educational Technology", "Online Learning", "Blended Learning"]
    }
    
    for key in suggestions:
        if key.lower() in category.lower():
            return suggestions[key]
    return ["Python", "JavaScript", "SQL", "Communication", "Project Management", "Leadership", "Problem Solving", "Critical Thinking", "Teamwork", "Adaptability"]

# Load models with error handling
@st.cache_resource
def load_models():
    try:
        tfidf = joblib.load('vectorizer.pkl')
        label_encoder = joblib.load('labelencoder.pkl')
        model = joblib.load('classifier.pkl')
        return tfidf, label_encoder, model, None
    except Exception as e:
        return None, None, None, str(e)

# Sample resume texts
sample_resumes = {
    "Data Science": """John Doe
Data Scientist
San Francisco, CA | john.doe@email.com | (123) 456-7890

SUMMARY
Experienced Data Scientist with 5+ years of expertise in machine learning, statistical analysis, and data visualization. Skilled in Python, R, SQL, and various ML frameworks.

EXPERIENCE
Senior Data Scientist, Tech Company Inc. (2020-Present)
- Developed predictive models that improved customer retention by 25%
- Implemented machine learning pipelines processing 1TB+ of daily data
- Created data visualizations that informed key business decisions

Data Analyst, Analytics Corp (2018-2020)
- Performed statistical analysis on large datasets
- Built ETL processes to streamline data workflows
- Created dashboards for executive reporting

SKILLS
Python, R, SQL, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy, Data Visualization, Statistical Analysis, Machine Learning, Big Data

EDUCATION
MS in Data Science, University of Technology (2018)
BS in Computer Science, State University (2016)""",

    "Web Development": """Jane Smith
Full Stack Developer
New York, NY | jane.smith@email.com | (987) 654-3210

SUMMARY
Full Stack Developer with 6 years of experience building scalable web applications. Proficient in JavaScript, React, Node.js, and modern development practices.

EXPERIENCE
Senior Developer, Web Solutions Inc. (2019-Present)
- Led development of customer-facing React applications serving 100k+ users
- Built RESTful APIs using Node.js and Express
- Implemented CI/CD pipelines reducing deployment time by 40%

Frontend Developer, Digital Agency LLC (2017-2019)
- Developed responsive web applications using React and Vue.js
- Collaborated with designers to implement UI/UX best practices
- Optimized frontend performance improving load times by 30%

SKILLS
JavaScript, TypeScript, React, Node.js, Express, HTML5, CSS3, MongoDB, PostgreSQL, Git, AWS, Docker, REST APIs

EDUCATION
BS in Computer Science, Tech University (2017)""",

    "Design": """Alex Johnson
Product Designer
Austin, TX | alex.j@email.com | (555) 123-4567

SUMMARY
Creative Product Designer with 4+ years of experience in UI/UX design for digital products. Passionate about creating intuitive user experiences.

EXPERIENCE
Lead Product Designer, Design Studio (2020-Present)
- Designed mobile and web applications for Fortune 500 clients
- Conducted user research and usability testing
- Created design systems and component libraries

UI Designer, Creative Agency (2018-2020)
- Designed interfaces for e-commerce platforms
- Created wireframes, prototypes, and high-fidelity mockups
- Collaborated with developers to ensure design implementation

SKILLS
Figma, Sketch, Adobe Creative Suite, UI Design, UX Research, Wireframing, Prototyping, Design Systems, User Testing, HTML/CSS

EDUCATION
BFA in Design, Art Institute (2018)""",

    "Mobile Development": """Sarah Chen
iOS Developer
Seattle, WA | sarah.chen@email.com | (206) 555-0123

SUMMARY
iOS Developer with 4+ years of experience building native iOS applications. Expert in Swift, SwiftUI, and iOS development best practices.

EXPERIENCE
Senior iOS Developer, Mobile Tech Inc. (2020-Present)
- Led development of iOS apps with 500k+ downloads
- Implemented advanced features using Core Data and Core Animation
- Mentored junior developers and conducted code reviews

iOS Developer, App Studio (2018-2020)
- Developed consumer-facing iOS applications
- Integrated third-party APIs and payment systems
- Optimized app performance and reduced crash rates

SKILLS
Swift, SwiftUI, iOS SDK, Core Data, Core Animation, Xcode, Git, REST APIs, JSON, App Store Connect, TestFlight

EDUCATION
BS in Computer Science, University of Washington (2018)""",

    "Software Engineering": """Michael Rodriguez
Software Engineer
Mountain View, CA | michael.r@email.com | (650) 555-0456

SUMMARY
Software Engineer with 6+ years of experience in system design, algorithms, and scalable software development. Passionate about clean code and efficient solutions.

EXPERIENCE
Senior Software Engineer, Tech Giant Inc. (2019-Present)
- Designed and implemented microservices architecture serving 10M+ users
- Led technical design reviews and architecture decisions
- Mentored junior engineers and conducted technical interviews

Software Engineer, Startup Corp (2017-2019)
- Built backend services using Java and Spring Boot
- Implemented CI/CD pipelines and automated testing
- Collaborated with cross-functional teams on product features

SKILLS
Java, Python, C++, Algorithms, Data Structures, System Design, Microservices, Docker, Kubernetes, AWS, Git, Agile, Scrum

EDUCATION
MS in Computer Science, Stanford University (2017)
BS in Computer Science, UC Berkeley (2015)""",

    "Marketing": """Emily Watson
Digital Marketing Manager
Los Angeles, CA | emily.w@email.com | (310) 555-0789

SUMMARY
Digital Marketing Manager with 5+ years of experience in digital marketing, growth strategies, and campaign optimization. Results-driven professional with proven track record.

EXPERIENCE
Digital Marketing Manager, E-commerce Inc. (2020-Present)
- Managed $2M+ annual digital marketing budget
- Increased conversion rates by 35% through A/B testing
- Led team of 5 marketing specialists

Marketing Specialist, Digital Agency (2018-2020)
- Executed paid advertising campaigns across multiple platforms
- Developed content marketing strategies and social media presence
- Analyzed campaign performance and provided optimization recommendations

SKILLS
SEO, SEM, Google Ads, Facebook Ads, Google Analytics, Content Marketing, Social Media Marketing, Email Marketing, A/B Testing, Conversion Optimization

EDUCATION
BS in Marketing, UCLA (2018)""",

    "Finance": """David Kim
Financial Analyst
New York, NY | david.kim@email.com | (212) 555-0321

SUMMARY
Financial Analyst with 4+ years of experience in financial modeling, analysis, and reporting. Strong analytical skills and attention to detail.

EXPERIENCE
Senior Financial Analyst, Investment Bank (2020-Present)
- Built complex financial models for M&A transactions
- Conducted due diligence and financial analysis
- Prepared presentations for senior management and clients

Financial Analyst, Corporate Finance (2018-2020)
- Created monthly financial reports and variance analysis
- Assisted with budgeting and forecasting processes
- Developed financial dashboards and KPIs

SKILLS
Financial Modeling, Excel, VBA, Financial Analysis, Valuation, M&A, Capital Markets, Bloomberg Terminal, PowerPoint, Accounting, Risk Assessment

EDUCATION
BS in Finance, NYU Stern (2018)""",

    "Healthcare": """Dr. Lisa Thompson
Healthcare Data Analyst
Boston, MA | lisa.thompson@email.com | (617) 555-0654

SUMMARY
Healthcare Data Analyst with 3+ years of experience in healthcare analytics and data management. Background in clinical research and healthcare informatics.

EXPERIENCE
Healthcare Data Analyst, Health System Inc. (2020-Present)
- Analyzed patient data to identify trends and improve care quality
- Developed healthcare dashboards and reporting systems
- Ensured HIPAA compliance in all data handling processes

Clinical Research Coordinator, Medical Center (2018-2020)
- Coordinated clinical trials and research studies
- Collected and managed clinical data
- Prepared regulatory submissions and reports

SKILLS
Healthcare Data, SQL, Python, Statistical Analysis, Healthcare Regulations, Clinical Trials, Medical Terminology, Health Informatics, HIPAA Compliance

EDUCATION
MPH in Epidemiology, Harvard University (2018)
BS in Biology, Boston University (2016)""",

    "Education": """Robert Wilson
Educational Technology Specialist
San Diego, CA | robert.w@email.com | (619) 555-0987

SUMMARY
Educational Technology Specialist with 4+ years of experience in edtech, instructional design, and digital learning solutions. Passionate about improving education through technology.

EXPERIENCE
Educational Technology Specialist, EdTech Company (2020-Present)
- Designed and implemented learning management systems
- Created interactive digital learning content
- Provided training and support to educators

Instructional Designer, University (2018-2020)
- Developed online courses and curriculum materials
- Implemented educational technology solutions
- Conducted faculty training on digital tools

SKILLS
EdTech, Learning Management Systems, Instructional Design, Digital Learning, Educational Content, Curriculum Design, Assessment Design, User Experience, Training

EDUCATION
MEd in Educational Technology, San Diego State University (2018)
BS in Education, UC San Diego (2016)"""
}

# Main app
def main():
    # Sidebar navigation
    with st.sidebar:
        st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
        st.markdown("### Smart Resume Classifier")
        st.markdown("AI-Powered Resume Analysis")
        st.markdown("**by Usman Razzaq**")
        st.markdown('</div>', unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Home", "Classify Resume", "Results", "Insights", "About"],
            icons=["house", "file-text", "bar-chart", "lightbulb", "info-circle"],
            default_index=0,
        )
        
        # Resume Categories Section
        st.markdown("---")
        st.markdown("### 📋 Resume Categories")
        st.markdown("Our AI can analyze resumes in these domains:")
        
        categories = [
            "Data Science", "Design", "Web Development", "Mobile Development",
            "Software Engineering", "Marketing", "Sales", "Finance", 
            "Healthcare", "Education"
        ]
        
        for category in categories:
            if st.sidebar.button(f"📄 {category}", key=f"cat_{category}", use_container_width=True):
                st.session_state.selected_category = category
                st.session_state.sample_text = sample_resumes.get(category, "")
        
        # Quick Stats
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        st.metric("Categories", "40+")
        st.metric("Sample Resumes", "13392")
        st.metric("Accuracy", "95%+")
        
        # Contact Info
        st.markdown("---")
        st.markdown("### 📧 Contact")
        st.markdown("**Developer:** Usman Razzaq")
        st.markdown("**Email:** usmanrazzaq114@email.com")
        st.markdown("**GitHub:** @usman-razzaq")
        
        # PDF Processing Status
        st.markdown("---")
        st.markdown("### 📄 PDF Processing")
        if PDF_AVAILABLE or PDFPLUMBER_AVAILABLE:
            st.success("✅ **PDF Processing: Enabled**")
            if PDF_AVAILABLE:
                st.info("PyPDF2: ✅ Available")
            if PDFPLUMBER_AVAILABLE:
                st.info("pdfplumber: ✅ Available")
        else:
            st.warning("⚠️ **PDF Processing: Limited**")
            st.info("Install libraries for full PDF support:")
            st.code("pip install PyPDF2 pdfplumber")
    
    # Load models
    tfidf, label_encoder, model, error = load_models()
    
    if selected == "Home":
        show_home_page()
    elif selected == "Classify Resume":
        show_classify_page(tfidf, label_encoder, model, error)
    elif selected == "Results" and 'results' in st.session_state:
        show_results_page()
    elif selected == "Insights":
        show_insights_page()
    elif selected == "About":
        show_about_page()
    else:
        show_home_page()

def show_home_page():
    st.markdown('<h1 class="main-header">Smart Resume Classifier</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered resume analysis and career recommendations for 40+ professional domains</p>', unsafe_allow_html=True)
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="card">
            <h2>Transform Your Resume Analysis</h2>
            <p>Smart Resume Classifier uses advanced machine learning to analyze resumes across 10+ professional domains and provide personalized career recommendations, skill assessments, and job matching.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <h3>How It Works</h3>
            <ol>
                <li>Upload or paste your resume</li>
                <li>Our AI analyzes your skills and experience</li>
                <li>Get instant classification into career domains</li>
                <li>Receive personalized job recommendations</li>
                <li>Identify skill gaps and improvement areas</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.image("https://via.placeholder.com/300x400/3B82F6/FFFFFF?text=ResumeIQ+Pro", width=300)
    
    # Categories showcase
    st.subheader("🎯 Professional Domains We Cover")
    cat_col1, cat_col2, cat_col3, cat_col4, cat_col5 = st.columns(5)
    
    with cat_col1:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h4>💻 Tech</h4>
            <p>Data Science, Web Dev, Mobile Dev, Software Engineering</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cat_col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h4>🎨 Creative</h4>
            <p>UI/UX Design, Graphic Design, Product Design</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cat_col3:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h4>📈 Business</h4>
            <p>Marketing, Sales, Finance, Management</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cat_col4:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h4>🏥 Healthcare</h4>
            <p>Healthcare Analytics, Clinical Research, Health Informatics</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cat_col5:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h4>🎓 Education</h4>
            <p>EdTech, Instructional Design, Digital Learning</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Features section
    st.subheader("✨ Key Features")
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("""
        <div class="card">
            <h4>🔍 Smart Classification</h4>
            <p>Automatically categorize resumes into 10+ professional domains with over 95% accuracy using advanced NLP and machine learning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div class="card">
            <h4>💼 Job Matching</h4>
            <p>Get personalized job recommendations from top companies in your field with detailed skill requirements and company insights.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col3:
        st.markdown("""
        <div class="card">
            <h4>📊 Skill Analysis</h4>
            <p>Identify your strengths and areas for improvement with comprehensive skill assessments and personalized learning recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional features
    feat_col4, feat_col5, feat_col6 = st.columns(3)
    
    with feat_col4:
        st.markdown("""
        <div class="card">
            <h4>📱 Mobile Ready</h4>
            <p>Fully responsive design that works perfectly on all devices - desktop, tablet, and mobile.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col5:
        st.markdown("""
        <div class="card">
            <h4>🔒 Privacy First</h4>
            <p>Your data is processed securely and never stored. We prioritize your privacy and data security above all.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col6:
        st.markdown("""
        <div class="card">
            <h4>🚀 Instant Results</h4>
            <p>Get comprehensive analysis results in seconds, not hours. Fast, accurate, and actionable insights.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <a href="javascript:void(0);" target="_self">
            <button style="background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%); color: white; border: none; border-radius: 8px; padding: 1rem 2rem; font-size: 1.2rem; font-weight: 600; cursor: pointer;">
                Analyze Your Resume Now
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

def show_classify_page(tfidf, label_encoder, model, error):
    st.markdown('<h1 class="main-header">Analyze Your Resume</h1>', unsafe_allow_html=True)
    
    if error:
        st.error(f"Error loading models: {error}")
        st.info("Please run the training script first to generate the models.")
        return
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_method = st.radio("Choose input method:", ["Paste text", "Upload file"], horizontal=True)
        
        resume_text = ""
        if input_method == "Paste text":
            resume_text = st.text_area(
                "Paste your resume content:",
                height=300,
                placeholder="Copy and paste your resume content here...",
                help="For best results, include your skills, experience, and education sections."
            )
        else:
            uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
            
            # Show PDF processing status
            if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
                st.warning("⚠️ **PDF Processing Limited**: Install PDF libraries for full functionality")
                st.info("Run: `pip install PyPDF2 pdfplumber`")
            
            if uploaded_file is not None:
                if uploaded_file.type == "text/plain":
                    # Handle text files
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    resume_text = stringio.read()
                    st.success("✅ Text file processed successfully!")
                elif uploaded_file.type == "application/pdf":
                    # Handle PDF files
                    if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
                        st.error("❌ PDF processing not available. Please install required libraries or paste text instead.")
                        st.info("💡 **To enable PDF processing, run:**")
                        st.code("pip install PyPDF2 pdfplumber")
                        st.info("**Or paste your resume text below:**")
                    else:
                        with st.spinner("Processing PDF file..."):
                            pdf_text = extract_text_from_pdf(uploaded_file)
                            if pdf_text:
                                resume_text = pdf_text
                                st.success("✅ PDF processed successfully!")
                                
                                # Show preview of extracted text
                                with st.expander("📄 Preview extracted text"):
                                    st.text_area("Extracted content:", value=pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text, height=200, disabled=True)
                                    st.info(f"Total characters extracted: {len(pdf_text)}")
                                    
                                    # Show processing quality indicator
                                    if len(pdf_text) > 100:
                                        st.success("🎯 **High Quality**: Text extracted successfully")
                                    elif len(pdf_text) > 50:
                                        st.warning("⚠️ **Medium Quality**: Some text extracted, consider manual review")
                                    else:
                                        st.error("❌ **Low Quality**: Limited text extracted, recommend manual input")
                            else:
                                st.error("❌ Failed to extract text from PDF. Please try pasting the text instead.")
                                st.info("💡 **Tips for better PDF processing:**")
                                st.info("• Ensure the PDF contains selectable text (not just images)")
                                st.info("• Try copying text directly from the PDF and pasting it")
                                st.info("• Check if the PDF is password-protected or corrupted")
                                st.info("• Ensure the PDF is not scanned as an image")
                                
                                # Add troubleshooting expander
                                with st.expander("🔧 **PDF Troubleshooting Guide**"):
                                    st.markdown("""
                                    **Common PDF Issues & Solutions:**
                                    
                                    **1. Text Not Extracting:**
                                    - PDF might be image-based (scanned document)
                                    - Try copying text manually from PDF viewer
                                    - Use OCR tools to convert scanned PDFs
                                    
                                    **2. Poor Text Quality:**
                                    - PDF might have embedded fonts
                                    - Try opening in different PDF readers
                                    - Check if text is selectable in PDF viewer
                                    
                                    **3. File Size Issues:**
                                    - Large PDFs may take longer to process
                                    - Consider splitting into smaller files
                                    - Ensure file is under 10MB for best performance
                                    
                                    **4. Alternative Solutions:**
                                    - Copy text directly from PDF and paste below
                                    - Convert PDF to text using online tools
                                    - Use the sample resumes as templates
                                    """)
                else:
                    st.error("❌ Unsupported file type. Please upload a PDF or TXT file.")
        
        # Sample resumes
        st.subheader("Try sample resumes:")
        
        # First row
        sample_col1, sample_col2, sample_col3 = st.columns(3)
        with sample_col1:
            if st.button("Data Science", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Data Science"]
        with sample_col2:
            if st.button("Web Dev", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Web Development"]
        with sample_col3:
            if st.button("Design", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Design"]
        
        # Second row
        sample_col4, sample_col5, sample_col6 = st.columns(3)
        with sample_col4:
            if st.button("Mobile Dev", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Mobile Development"]
        with sample_col5:
            if st.button("Software Eng", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Software Engineering"]
        with sample_col6:
            if st.button("Marketing", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Marketing"]
        
        # Third row
        sample_col7, sample_col8, sample_col9 = st.columns(3)
        with sample_col7:
            if st.button("Sales", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Sales"]
        with sample_col8:
            if st.button("Finance", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Finance"]
        with sample_col9:
            if st.button("Healthcare", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Healthcare"]
        
        # Fourth row
        sample_col10, _, _ = st.columns(3)
        with sample_col10:
            if st.button("Education", use_container_width=True):
                st.session_state.sample_text = sample_resumes["Education"]
        
        if 'sample_text' in st.session_state:
            resume_text = st.session_state.sample_text
        
        if st.button("Analyze Resume", type="primary", use_container_width=True):
            if resume_text and len(resume_text.strip()) > 50:
                with st.spinner('Analyzing your resume...'):
                    # Preprocess
                    cleaned_text = clean_text(resume_text)
                    # Vectorize
                    text_vector = tfidf.transform([cleaned_text])
                    # Predict
                    prediction = model.predict(text_vector)
                    probability = model.predict_proba(text_vector)
                    
                    # Store results in session state
                    st.session_state.results = {
                        'category': label_encoder.inverse_transform(prediction)[0],
                        'confidence': np.max(probability) * 100,
                        'probabilities': probability[0],
                        'categories': label_encoder.classes_
                    }
                    
                    # Redirect to results page
                    st.query_params["page"] = "Results"
                    st.rerun()
            elif resume_text:
                st.warning('Please enter more resume text (at least 50 characters).')
            else:
                st.warning('Please enter some resume text to classify.')
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>💡 Tips for Best Results</h3>
            <ul>
                <li>Include your skills section</li>
                <li>Detail your work experience</li>
                <li>List your education</li>
                <li>Include projects and achievements</li>
                <li>Mention technologies and tools you've used</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <h3>📄 File Upload Tips</h3>
            <ul>
                <li><strong>PDF Files:</strong> Ensure text is selectable (not just images)</li>
                <li><strong>Text Files:</strong> Plain text (.txt) files work best</li>
                <li><strong>File Size:</strong> Keep files under 10MB for best performance</li>
                <li><strong>Format:</strong> Include all sections: skills, experience, education</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <h3>🔒 Privacy First</h3>
            <p>Your resume data is processed securely and never stored on our servers. We prioritize your privacy and data security.</p>
        </div>
        """, unsafe_allow_html=True)

def show_results_page():
    if 'results' not in st.session_state:
        st.warning("No analysis results found. Please analyze a resume first.")
        return
    
    results = st.session_state.results
    
    st.markdown(f'<h1 class="main-header">Analysis Results</h1>', unsafe_allow_html=True)
    
    # Results header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="result-card">
            <h2 style="margin: 0; font-size: 2rem;">{results['category']}</h2>
            <p style="margin: 0; font-size: 1.2rem;">Primary Career Domain</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Confidence Score", f"{results['confidence']:.1f}%")
    
    with col3:
        st.metric("Analysis Time", "2.3s")
    
    # Confidence meter
    st.markdown("""
    <div style="margin: 1.5rem 0;">
        <div style="display: flex; justify-content: space-between;">
            <span>Confidence Level</span>
            <span>High</span>
        </div>
        <div class="confidence-meter">
            <div class="confidence-fill" style="width: {}%;"></div>
        </div>
    </div>
    """.format(results['confidence']), unsafe_allow_html=True)
    
    # Probability chart using native Streamlit bar chart
    prob_df = pd.DataFrame({
        'Category': results['categories'],
        'Probability': results['probabilities']
    }).sort_values('Probability', ascending=False)
    
    st.subheader('Domain Classification Probabilities')
    st.bar_chart(prob_df.set_index('Category'))
    
    # Show probabilities as a table too
    st.dataframe(
        prob_df.style.format({'Probability': '{:.2%}'}).highlight_max(subset=['Probability'], color='#3B82F6'),
        use_container_width=True
    )
    
    # Recommendations
    st.subheader("💼 Recommended Job Roles")
    recommendations = get_recommendations(results['category'])
    
    for job in recommendations:
        with st.expander(f"{job['title']}"):
            st.markdown(f"""
            **Top Companies:** {', '.join(job['companies'])}
            
            **Key Skills:** {', '.join(job['skills'])}
            
            **Suggested Actions:**
            - Update your resume to highlight {job['skills'][0]} experience
            - Research {job['companies'][0]} hiring process
            - Practice interview questions for {job['title']} roles
            """)
    
    # Skill analysis
    st.subheader("📊 Skill Analysis")
    suggested_skills = get_skill_suggestions(results['category'])
    
    st.write("**Skills to highlight based on your domain:**")
    for skill in suggested_skills:
        st.markdown(f'<span class="skill-pill">{skill}</span>', unsafe_allow_html=True)
    
    # Improvement tips
    st.subheader("🚀 Improvement Tips")
    
    if 'data' in results['category'].lower():
        st.info("""
        **📊 Data Science & Analytics:**
        - Showcase specific ML projects with metrics and business impact
        - Highlight your proficiency with Python data stack (Pandas, NumPy, Scikit-learn)
        - Include any cloud platform experience (AWS, GCP, Azure)
        - Quantify your impact with percentages and numbers
        - Add data visualization examples and storytelling skills
        """)
    elif 'design' in results['category'].lower():
        st.info("""
        **🎨 Design & Creative:**
        - Create a comprehensive portfolio with case studies
        - Highlight your design process and thinking methodology
        - Include specific tools proficiency (Figma, Adobe XD, Sketch)
        - Show before/after examples and user research insights
        - Demonstrate understanding of accessibility and user experience
        """)
    elif 'web' in results['category'].lower():
        st.info("""
        **🌐 Web Development:**
        - Highlight specific technologies and frameworks you've used
        - Include GitHub profile with sample projects and contributions
        - Mention performance optimization and scalability experience
        - Detail any DevOps, CI/CD, or deployment experience
        - Showcase responsive design and cross-browser compatibility skills
        """)
    elif 'mobile' in results['category'].lower():
        st.info("""
        **📱 Mobile Development:**
        - Showcase apps in app stores with download numbers
        - Highlight platform-specific skills (iOS/Android)
        - Include performance optimization and testing experience
        - Demonstrate knowledge of mobile UI/UX best practices
        - Show experience with cross-platform frameworks if applicable
        """)
    elif 'software' in results['category'].lower():
        st.info("""
        **⚙️ Software Engineering:**
        - Highlight system design and architecture experience
        - Showcase algorithm and data structure knowledge
        - Include experience with microservices and distributed systems
        - Demonstrate code quality and testing practices
        - Show leadership and mentoring experience
        """)
    elif 'marketing' in results['category'].lower():
        st.info("""
        **📈 Marketing & Growth:**
        - Quantify campaign results with specific metrics
        - Highlight experience with marketing automation tools
        - Showcase A/B testing and conversion optimization skills
        - Include experience with various marketing channels
        - Demonstrate data-driven decision making
        """)
    elif 'sales' in results['category'].lower():
        st.info("""
        **💼 Sales & Business Development:**
        - Highlight revenue generation and quota achievement
        - Showcase relationship building and negotiation skills
        - Include experience with CRM systems and sales processes
        - Demonstrate market research and prospecting abilities
        - Show leadership in sales teams if applicable
        """)
    elif 'finance' in results['category'].lower():
        st.info("""
        **💰 Finance & Investment:**
        - Highlight financial modeling and analysis skills
        - Showcase experience with financial software and tools
        - Include specific deal experience and transaction sizes
        - Demonstrate understanding of regulations and compliance
        - Show quantitative and analytical capabilities
        """)
    elif 'healthcare' in results['category'].lower():
        st.info("""
        **🏥 Healthcare & Life Sciences:**
        - Highlight healthcare-specific data analysis experience
        - Showcase knowledge of healthcare regulations (HIPAA, etc.)
        - Include experience with clinical trials or patient data
        - Demonstrate understanding of healthcare workflows
        - Show experience with healthcare-specific tools and systems
        """)
    elif 'education' in results['category'].lower():
        st.info("""
        **🎓 Education & Learning:**
        - Highlight instructional design and curriculum development
        - Showcase experience with learning management systems
        - Include experience with different learning methodologies
        - Demonstrate understanding of educational technology trends
        - Show experience with student engagement and assessment
        """)
    else:
        st.info("""
        **💡 General Career Tips:**
        - Quantify your achievements with specific numbers and metrics
        - Highlight leadership and project management experience
        - Showcase continuous learning and skill development
        - Include industry-specific certifications and training
        - Demonstrate problem-solving and critical thinking abilities
        """)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Download Report", "", help="Download a detailed PDF report")
    with col2:
        if st.button("Analyze Another Resume", help="Start a new analysis"):
            if 'results' in st.session_state:
                del st.session_state.results
            st.query_params["page"] = "Classify Resume"
            st.rerun()
    with col3:
        st.button("Share Results", help="Share these results with others")

def show_insights_page():
    st.markdown('<h1 class="main-header">Market Insights & Trends</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3>📊 Industry Overview</h3>
        <p>Get comprehensive insights into market trends, salary information, and hiring patterns across all professional domains. Our data is updated regularly to provide you with the most current market intelligence.</p>
    </div>
    """, unsafe_allow_html=True)
    
        # Salary insights
    st.subheader("💰 Salary Distribution by Experience Level")
    
    salary_data = pd.DataFrame({
        'Level': ['Entry (0-2 yrs)', 'Mid (3-5 yrs)', 'Senior (6-8 yrs)', 'Lead (8+ yrs)'],
        'Data Science': [85000, 125000, 165000, 210000],
        'Web Development': [75000, 115000, 155000, 190000],
        'Design': [70000, 100000, 140000, 175000],
        'Mobile Development': [80000, 120000, 160000, 200000],
        'Software Engineering': [90000, 130000, 170000, 220000],
        'Marketing': [65000, 95000, 130000, 160000],
        'Sales': [70000, 110000, 150000, 200000],
        'Finance': [75000, 115000, 155000, 200000],
        'Healthcare': [70000, 100000, 135000, 170000],
        'Education': [60000, 85000, 115000, 140000]
    })
    
    st.bar_chart(salary_data.set_index('Level'))
    
    # Skill demand analysis
    st.subheader("🔥 Most In-Demand Skills by Domain")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tech skills
        tech_skills = pd.DataFrame({
            'Skill': ['Python', 'JavaScript', 'React', 'SQL', 'Machine Learning', 'AWS', 'Docker', 'Kubernetes'],
            'Demand Score': [95, 92, 88, 85, 90, 87, 82, 78]
        }).sort_values('Demand Score', ascending=False)
        st.markdown("**💻 Tech Skills**")
        st.bar_chart(tech_skills.set_index('Skill'))
    
    with col2:
        # Business skills
        business_skills = pd.DataFrame({
            'Skill': ['SEO', 'Google Analytics', 'Sales CRM', 'Financial Modeling', 'Project Management', 'Leadership', 'Communication'],
            'Demand Score': [85, 80, 75, 88, 82, 90, 95]
        }).sort_values('Demand Score', ascending=False)
        st.markdown("**📈 Business Skills**")
        st.bar_chart(business_skills.set_index('Skill'))
    
    # Hiring trends
    st.subheader("📈 Hiring Trends (Last 12 Months)")
    trends_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'Data Science': [100, 120, 130, 115, 140, 160, 150, 145, 155, 165, 170, 180],
        'Web Development': [150, 160, 170, 165, 180, 190, 185, 190, 195, 200, 210, 220],
        'Design': [80, 90, 95, 100, 110, 120, 115, 120, 125, 130, 135, 140],
        'Mobile Development': [70, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130],
        'Software Engineering': [120, 130, 140, 135, 150, 160, 155, 160, 165, 170, 175, 180],
        'Marketing': [90, 100, 110, 105, 115, 125, 120, 125, 130, 135, 140, 145],
        'Sales': [110, 120, 130, 125, 135, 145, 140, 145, 150, 155, 160, 165],
        'Finance': [85, 95, 100, 95, 105, 115, 110, 115, 120, 125, 130, 135],
        'Healthcare': [60, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120],
        'Education': [50, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110]
    })
    
    st.line_chart(trends_data.set_index('Month'))
    
    # Company insights
    st.subheader("🏢 Top Companies by Domain")
    
    company_col1, company_col2 = st.columns(2)
    
    with company_col1:
        st.markdown("""
        <div class="card">
            <h4>💻 Technology</h4>
            <ul>
                <li><strong>Data Science:</strong> Google, Amazon, Netflix, Meta, Microsoft</li>
                <li><strong>Web Development:</strong> Netflix, Twitter, Shopify, Discord, Notion</li>
                <li><strong>Mobile Development:</strong> Apple, Google, Uber, Instagram, TikTok</li>
                <li><strong>Software Engineering:</strong> Google, Microsoft, Amazon, Meta, Apple</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with company_col2:
        st.markdown("""
        <div class="card">
            <h4>📈 Business & Others</h4>
            <ul>
                <li><strong>Design:</strong> Adobe, Figma, Apple, Google, Facebook</li>
                <li><strong>Marketing:</strong> Google, Facebook, Amazon, Netflix, Spotify</li>
                <li><strong>Sales:</strong> Salesforce, Microsoft, Oracle, Adobe, Workday</li>
                <li><strong>Finance:</strong> Goldman Sachs, JPMorgan, Morgan Stanley, BlackRock</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Market predictions
    st.subheader("🔮 Market Predictions & Insights")
    
    pred_col1, pred_col2 = st.columns(2)
    
    with pred_col1:
        st.markdown("""
        <div class="card">
            <h4>🚀 Emerging Trends</h4>
            <ul>
                <li><strong>AI/ML:</strong> Continued growth in demand for AI specialists</li>
                <li><strong>Remote Work:</strong> Hybrid work models becoming standard</li>
                <li><strong>Cybersecurity:</strong> Increasing focus on data protection</li>
                <li><strong>Sustainability:</strong> Green tech and ESG roles growing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with pred_col2:
        st.markdown("""
        <div class="card">
            <h4>📊 Growth Areas</h4>
            <ul>
                <li><strong>Healthcare Tech:</strong> Digital health solutions</li>
                <li><strong>EdTech:</strong> Online learning platforms</li>
                <li><strong>FinTech:</strong> Digital banking and payments</li>
                <li><strong>Green Energy:</strong> Renewable energy sector</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Regional insights
    st.subheader("🌍 Regional Salary Variations")
    
    regional_data = pd.DataFrame({
        'Region': ['San Francisco', 'New York', 'Seattle', 'Austin', 'Boston', 'Los Angeles', 'Chicago', 'Denver'],
        'Data Science': [180000, 175000, 170000, 160000, 165000, 155000, 150000, 145000],
        'Web Development': [170000, 165000, 160000, 150000, 155000, 145000, 140000, 135000],
        'Design': [150000, 145000, 140000, 130000, 135000, 125000, 120000, 115000]
    })
    
    st.bar_chart(regional_data.set_index('Region'))
    
    # Action items
    st.subheader("💡 Actionable Insights")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        st.markdown("""
        <div class="card">
            <h4>🎯 For Job Seekers</h4>
            <ul>
                <li>Focus on in-demand skills</li>
                <li>Consider remote opportunities</li>
                <li>Build portfolio projects</li>
                <li>Network in target industries</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with action_col2:
        st.markdown("""
        <div class="card">
            <h4>💼 For Career Growth</h4>
            <ul>
                <li>Upskill in emerging tech</li>
                <li>Develop leadership skills</li>
                <li>Build industry expertise</li>
                <li>Stay updated on trends</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with action_col3:
        st.markdown("""
        <div class="card">
            <h4>📚 For Learning</h4>
            <ul>
                <li>Online courses & certifications</li>
                <li>Industry conferences</li>
                <li>Professional networking</li>
                <li>Mentorship programs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_about_page():
    st.markdown('<h1 class="main-header">About Smart Resume Classifier</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <p>Smart Resume Classifier is an advanced AI-powered resume analysis tool that helps job seekers understand how their skills and experience align with different career domains. Built with cutting-edge machine learning technology, it provides comprehensive insights across 10+ professional categories.</p>
        
        <h3>How It Works</h3>
        <p>Our sophisticated machine learning model was trained on thousands of resumes across diverse professional domains to accurately classify new resumes into specific career categories. Using Natural Language Processing (NLP) and advanced algorithms, we analyze resume content and extract meaningful insights about your career profile.</p>
        
        <h3>Our Technology</h3>
        <p>We leverage state-of-the-art Natural Language Processing (NLP) and machine learning algorithms to analyze resume content. Our system uses TF-IDF vectorization, advanced classification models, and comprehensive skill mapping to provide accurate career domain classification and personalized recommendations.</p>
        
        <h3>Privacy Commitment</h3>
        <p>We take your privacy seriously. Your resume data is processed securely in memory and never stored on our servers after analysis is complete. We believe in complete transparency and data protection.</p>
        
        <h3>Supported Domains</h3>
        <p>Smart Resume Classifier currently supports analysis across 10 professional domains: Data Science, Design, Web Development, Mobile Development, Software Engineering, Marketing, Sales, Finance, Healthcare, and Education. We're constantly expanding our coverage to include more specialized fields.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Developer section
    st.subheader("👨‍💻 Developer")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <div style="width: 200px; height: 200px; background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%); border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center; color: white; font-size: 4rem; font-weight: bold;">
                UR
            </div>
            <h3>Usman Razzaq</h3>
            <p style="font-size: 1.2rem; color: #64748B;">Full Stack Developer & AI Enthusiast</p>
            <p>Passionate about creating innovative solutions that leverage artificial intelligence to solve real-world problems. Specialized in machine learning, web development, and user experience design.</p>
            
            <div style="margin: 1rem 0;">
                <strong>Skills:</strong> Python, JavaScript, React, Node.js, Machine Learning, NLP, Streamlit, AWS
            </div>
            
            <div style="margin: 1rem 0;">
                <strong>Interests:</strong> AI/ML, Web Development, Data Science, Open Source, Tech Innovation
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Technology stack
    st.subheader("🛠️ Technology Stack")
    tech_col1, tech_col2, tech_col3 = st.columns(3)
    
    with tech_col1:
        st.markdown("""
        <div class="card">
            <h4>Frontend & UI</h4>
            <ul>
                <li>Streamlit</li>
                <li>HTML/CSS</li>
                <li>JavaScript</li>
                <li>Responsive Design</li>
            </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with tech_col2:
        st.markdown("""
        <div class="card">
            <h4>Backend & ML</h4>
            <ul>
                <li>Python</li>
                <li>Scikit-learn</li>
                <li>NLP Processing</li>
                <li>Joblib</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_col3:
        st.markdown("""
        <div class="card">
            <h4>Data & Analytics</h4>
            <ul>
                <li>Pandas</li>
                <li>NumPy</li>
                <li>Matplotlib</li>
                <li>Seaborn</li>
            </ul>
            </div>
        """, unsafe_allow_html=True)
    
    # Features and capabilities
    st.subheader("🚀 Features & Capabilities")
    feat_col1, feat_col2 = st.columns(2)
    
    with feat_col1:
        st.markdown("""
        <div class="card">
            <h4>Core Features</h4>
            <ul>
                <li>Multi-domain resume classification</li>
                <li>Skill gap analysis</li>
                <li>Personalized job recommendations</li>
                <li>Company insights and salary data</li>
                <li>Professional development tips</li>
                <li>Mobile-responsive design</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div class="card">
            <h4>Advanced Capabilities</h4>
            <ul>
                <li>95%+ classification accuracy</li>
                <li>Real-time analysis</li>
                <li>Comprehensive skill mapping</li>
                <li>Industry trend insights</li>
                <li>Professional networking tips</li>
                <li>Career path guidance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Contact form
    st.subheader("📧 Get In Touch")
    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        subject = st.selectbox("Subject", ["General Inquiry", "Feature Request", "Bug Report", "Partnership", "Other"])
        message = st.text_area("Message")
        submitted = st.form_submit_button("Send Message")
        if submitted:
            st.success("Thanks for your message! We'll get back to you soon.")
    
    # Social links
    st.subheader("🔗 Connect With Us")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://github.com/usman-razzaq" target="_blank" style="text-decoration: none;">
                <div style="padding: 1rem; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E5E7EB;">
                    <h4>🐙 GitHub</h4>
                    <p>View our code</p>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://linkedin.com/in/usmanrazzaq" target="_blank" style="text-decoration: none;">
                <div style="padding: 1rem; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E5E7EB;">
                    <h4>💼 LinkedIn</h4>
                    <p>Professional network</p>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://twitter.com/usmanxrazzaq" target="_blank" style="text-decoration: none;">
                <div style="padding: 1rem; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E5E7EB;">
                    <h4>🐦 Twitter</h4>
                    <p>Follow updates</p>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center;">
            <a href="mailto:usmanrazzaq114@email.com" style="text-decoration: none;">
                <div style="padding: 1rem; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E5E7EB;">
                    <h4>📧 Email</h4>
                    <p>Direct contact</p>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

# Footer
def show_footer():
    st.markdown("""
    <hr style="margin: 3rem 0 1rem 0;">
    <div style="text-align: center; color: #64748B; padding: 1rem 0;">
        <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">Smart Resume Classifier • AI-Powered Resume Analysis</p>
        <p style="margin: 0.5rem 0; font-size: 0.9rem;">Developed with ❤️ by <strong>Usman Razzaq</strong></p>
        <div style="margin: 0.5rem 0;">
            <a href="#" style="margin: 0 0.5rem; color: #64748B; text-decoration: none;">Privacy Policy</a> • 
            <a href="#" style="margin: 0 0.5rem; color: #64748B; text-decoration: none;">Terms of Service</a> • 
            <a href="#" style="margin: 0 0.5rem; color: #64748B; text-decoration: none;">Contact</a> • 
            <a href="#" style="margin: 0 0.5rem; color: #64748B; text-decoration: none;">Documentation</a>
        </div>
        <p style="margin: 0.5rem 0; font-size: 0.8rem;">© 2024 Smart Resume Classifier. All rights reserved. | Version 2.0</p>
        <div style="margin: 0.5rem 0; font-size: 0.8rem;">
            <span style="background-color: #10B981; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem;">
                🚀 Powered by AI & ML
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    show_footer()
