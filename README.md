# 📚 Kitap AI - Mind Map Generator

> Transform your knowledge into beautiful, interactive mind maps using AI

Kitap AI is a powerful web application that helps you create, visualize, and organize information through AI-powered mind maps. Whether you're processing PDF documents, generating mind maps from prompts, or organizing your thoughts, Kitap AI makes knowledge visualization simple and intuitive.

## ✨ Features

### 🤖 AI-Powered Generation
- **Smart PDF Processing**: Extract chapters from PDF documents and automatically generate mind maps
- **Prompt-Based Generation**: Create mind maps from text descriptions and topics
- **Multi-Language Support**: Generate mind maps in multiple languages (English, Russian, Spanish, French, German, Italian, Portuguese, Chinese, Japanese)

### 📊 Interactive Mind Maps
- **Real-Time Preview**: See your mind maps update as you edit
- **Full-Screen Mode**: Immersive viewing experience
- **Responsive Design**: Works perfectly on desktop and mobile devices

### 💾 Export Options
- **Markdown Export**: Download your mind maps as `.md` files
- **HTML Export**: Interactive HTML files for sharing
- **Obsidian Canvas**: Export to Obsidian Canvas format

### 👤 User Management
- **Secure Authentication**: User registration and login system
- **Personal Dashboard**: Manage all your mind maps in one place
- **Cloud Storage**: Your mind maps are safely stored in the cloud

### 🎨 Modern UI/UX
- **Clean Interface**: Beautiful, modern design with intuitive navigation
- **Dark/Light Theme**: Comfortable viewing in any environment
- **Responsive Layout**: Optimized for all screen sizes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (for AI features)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/kitap-ai.git
cd kitap-ai
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
IS_PRODUCTION=false
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser**
Navigate to `http://localhost:8501`

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) - Interactive web applications
- **Mind Map Visualization**: [streamlit-markmap](https://github.com/streamlit/streamlit-markmap) - Interactive mind map rendering
- **AI Integration**: [OpenAI GPT](https://openai.com/) - Smart content generation
- **Database**: SQLite with SQLAlchemy ORM
- **PDF Processing**: Custom PDF chapter extraction
- **Export Formats**: HTML, Markdown, Obsidian Canvas

## 📖 Usage Guide

### Creating Your First Mind Map

1. **Register/Login**: Create an account or log in to access your dashboard
2. **Choose Creation Method**:
   - **Create New**: Start with a blank mind map
   - **Import from File**: Upload a PDF or Markdown file
   - **Generate from Prompt**: Use AI to create mind maps from descriptions

### Working with PDFs

1. Upload your PDF document
2. The system automatically extracts chapters
3. AI processes each chapter to create structured mind maps
4. Review and edit the generated content
5. Export in your preferred format

### AI Prompt Generation

1. Enter a topic and detailed description
2. Select your preferred language
3. Let AI generate a comprehensive mind map
4. Edit and customize as needed

### Dashboard Features

- **View All Mind Maps**: Browse your complete collection
- **Quick Actions**: Edit, view, export, or delete mind maps
- **Search & Filter**: Find specific mind maps quickly
- **Export Options**: Download in multiple formats

## 🏗️ Project Structure

```
kitap-ai/
├── app.py                 # Main Streamlit application
├── mindmap_generator.py   # AI mind map generation logic
├── pdf_mindmap_generator.py # PDF processing and chapter extraction
├── database.py           # Database models and operations
├── canvas_exporter.py    # Obsidian Canvas export functionality
├── html_exporter.py      # HTML export functionality
├── requirements.txt      # Python dependencies
├── logo.png             # Application logo
├── logo.svg             # Vector logo
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `IS_PRODUCTION` | Production mode flag | `false` |

### Database

The application uses SQLite by default. The database is automatically initialized on first run.

## 📱 Screenshots

### Dashboard
*Clean, organized interface for managing your mind maps*

### Mind Map Editor
*Real-time editing with live preview*

### AI Generation
*Smart mind map creation from prompts*

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add some amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

1. Follow the installation steps above
2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```
3. Run tests:
```bash
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/yourusername/kitap-ai/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/kitap-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/kitap-ai/discussions)

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [OpenAI](https://openai.com/) for powerful AI capabilities
- [Markmap](https://markmap.js.org/) for beautiful mind map visualization
- All contributors who help make this project better

## 🔮 Roadmap

- [ ] Real-time collaboration features
- [ ] Advanced export options (PNG, SVG)
- [ ] Integration with more AI models
- [ ] Mobile app development
- [ ] Advanced mind map templates
- [ ] Team workspaces

---

<div align="center">
  <p>Made with ❤️ for knowledge visualization</p>
  <p>
    <a href="https://github.com/yourusername/kitap-ai">⭐ Star us on GitHub</a> |
    <a href="https://twitter.com/yourusername">🐦 Follow on Twitter</a> |
    <a href="https://linkedin.com/in/yourusername">💼 Connect on LinkedIn</a>
  </p>
</div> 