Smart Lost and Found Item Recovery System
📌 Project Overview
The Smart Lost and Found Item Recovery System is a web-based platform designed to efficiently manage the process of reporting, tracking, and recovering lost or found items within an institution or community. By replacing traditional manual methods like logbooks and notice boards, the system provides a centralized digital portal that enhances transparency, accessibility, and the success rate of item recovery.
🚀 Key Features
• User Authentication: Secure registration and login with email verification and OTP (One-Time Password) workflows.
• Reporting System: Users can report lost or found items with detailed descriptions, categories, locations, and optional images/videos.
• AI-Based Matching: Utilizes an intelligent matching engine that compares reports based on text similarity and YOLOv8 image-based object detection.
• Admin Dashboard: A dedicated interface for administrators to verify AI-suggested matches, manage item statuses (e.g., "Handover" or "Returned"), and view system-wide statistics.
• Automated Notifications: Instant email or SMS confirmations are sent to users once a report is filed or a potential match is identified.
• Data Security: Implementation of secure password hashing (bcrypt) and encrypted data transfers (HTTPS).
🛠️ Tech Stack
• Backend: Django (Python).
• Database: MongoDB (NoSQL) for flexible data storage of unstructured item descriptions and images.
• Frontend: HTML, CSS, JavaScript, and Bootstrap.
• AI/ML: YOLOv8 (for object detection) and text similarity algorithms.
• Communication: SMTP for email notifications.
📈 Methodology & Metrics
• Agile/Scrum Framework: The project followed an iterative development process focusing on flexibility and user-centric design.
• Effort Estimation: Calculated using the COCOMO model (estimated at ~15.52 person-months) and Function Point (FP) analysis (120 FP).
• Testing: Validated through both Black-Box and White-Box testing methodologies to ensure functional accuracy and logical reliability.
🌍 Sustainable Development Goals (SDG) Mapping
This project aligns with the following UN Sustainable Development Goals:
• Goal 11 (Sustainable Cities and Communities): Enhancing safety and responsibility through simplified item recovery.
• Goal 12 (Responsible Consumption and Production): Promoting the reuse and recovery of assets, thereby minimizing waste.
• Goal 16 (Peace, Justice, and Strong Institutions): Establishing transparency through digital record-keeping and audit logs.
📂 Project Structure
• users/: Handles user registration, profiles, and dashboards.
• items/: Manages the reporting and listing of lost and found items.
• adminpanel/: Controls verification workflows and system analytics.
• ai_module/: Contains the matching logic and similarity scoring algorithms
