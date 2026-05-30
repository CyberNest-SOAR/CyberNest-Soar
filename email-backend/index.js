const express = require("express");
const nodemailer = require("nodemailer");
const cors = require("cors");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// API Endpoint
app.post("/api/request-demo", async (req, res) => {
  const { name, email, company, message } = req.body;

  if (!name || !email || !company) {
    return res.status(400).json({ 
      success: false, 
      message: "Please provide name, email, and company." 
    });
  }

  // Create Transporter
  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  // Email Options
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: "cybernestsoar@gmail.com",
    subject: "New Demo Request",
    html: `
      <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #6366F1;">New Demo Request Received</h2>
        <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 20px;" />
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Company:</strong> ${company}</p>
        <p><strong>Message:</strong> ${message || "N/A"}</p>
        <br />
        <p style="font-size: 12px; color: #999;">This email was sent from the CyberNest SOAR landing page form.</p>
      </div>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log("Email sent successfully to:", mailOptions.to);
    res.status(200).json({ success: true, message: "Email sent successfully" });
  } catch (error) {
    console.error("Nodemailer Error:", error);
    res.status(500).json({ success: false, message: "Failed to send email" });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
