/**
 * DataShield AI — DataShieldAudit Contract Tests
 *
 * Comprehensive test suite covering deployment, access-event logging,
 * automatic and manual alert creation, alert resolution, threshold
 * management, getter functions, and event emission.
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DataShieldAudit", function () {
  let contract;
  let owner;
  let addr1;
  let addr2;

  // Convenience: a deterministic event hash for testing
  const sampleHash = ethers.keccak256(ethers.toUtf8Bytes("sample-event-001"));
  const sampleHash2 = ethers.keccak256(ethers.toUtf8Bytes("sample-event-002"));
  const sampleHash3 = ethers.keccak256(ethers.toUtf8Bytes("sample-event-003"));

  /**
   * Deploy a fresh contract before each test so tests are independent.
   */
  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("DataShieldAudit");
    contract = await Factory.deploy();
    await contract.waitForDeployment();
  });

  // ─────────────────── Deployment ─────────────────────────────────────────

  describe("Deployment", function () {
    it("should set the deployer as the owner", async function () {
      expect(await contract.owner()).to.equal(owner.address);
    });

    it("should initialize the alert threshold to 70", async function () {
      expect(await contract.alertThreshold()).to.equal(70);
    });

    it("should start with zero events and zero alerts", async function () {
      expect(await contract.getEventCount()).to.equal(0);
      expect(await contract.getAlertCount()).to.equal(0);
    });
  });

  // ─────────────────── Logging Access Events ──────────────────────────────

  describe("logAccessEvent", function () {
    it("should log an access event and store it correctly", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_42", "SELECT", "prod.users", 30, "QmFakeHash"
      );

      const evt = await contract.getAccessEvent(sampleHash);
      expect(evt.eventHash).to.equal(sampleHash);
      expect(evt.userId).to.equal("user_42");
      expect(evt.action).to.equal("SELECT");
      expect(evt.tableName).to.equal("prod.users");
      expect(evt.threatScore).to.equal(30);
      expect(evt.ipfsReportHash).to.equal("QmFakeHash");
      expect(evt.timestamp).to.be.greaterThan(0);
    });

    it("should increment event count", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_1", "SELECT", "prod.users", 10, ""
      );
      expect(await contract.getEventCount()).to.equal(1);

      await contract.logAccessEvent(
        sampleHash2, "user_2", "DELETE", "prod.payments", 50, ""
      );
      expect(await contract.getEventCount()).to.equal(2);
    });

    it("should reject duplicate event hashes", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_1", "SELECT", "prod.users", 10, ""
      );
      await expect(
        contract.logAccessEvent(sampleHash, "user_2", "DELETE", "prod.users", 20, "")
      ).to.be.revertedWith("DataShieldAudit: event hash already logged");
    });

    it("should reject zero event hash", async function () {
      await expect(
        contract.logAccessEvent(
          ethers.ZeroHash, "user_1", "SELECT", "prod.users", 10, ""
        )
      ).to.be.revertedWith("DataShieldAudit: event hash cannot be zero");
    });

    it("should reject threat score above 100", async function () {
      await expect(
        contract.logAccessEvent(sampleHash, "user_1", "SELECT", "t", 101, "")
      ).to.be.revertedWith("DataShieldAudit: threat score must be 0-100");
    });

    it("should emit AccessEventLogged event", async function () {
      await expect(
        contract.logAccessEvent(sampleHash, "user_42", "DELETE", "prod.ssn", 55, "Qm123")
      )
        .to.emit(contract, "AccessEventLogged")
        .withArgs(sampleHash, "user_42", 55, (ts) => ts > 0n);
    });
  });

  // ─────────────────── Auto-Alert Creation ────────────────────────────────

  describe("Auto-alert on high threat score", function () {
    it("should auto-create an alert when score >= threshold (70)", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_bad", "DELETE", "prod.ssn_data", 85, "QmReport"
      );

      expect(await contract.getAlertCount()).to.equal(1);
      const alert = await contract.getThreatAlert(1);
      expect(alert.eventHash).to.equal(sampleHash);
      expect(alert.threatLevel).to.equal("HIGH");
      expect(alert.resolved).to.equal(false);
    });

    it("should label CRITICAL for score >= 90", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_bad", "DROP", "prod.users", 95, ""
      );
      const alert = await contract.getThreatAlert(1);
      expect(alert.threatLevel).to.equal("CRITICAL");
    });

    it("should label MEDIUM for score 70-79", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_x", "UPDATE", "prod.users", 72, ""
      );
      const alert = await contract.getThreatAlert(1);
      expect(alert.threatLevel).to.equal("MEDIUM");
    });

    it("should NOT auto-create an alert when score < threshold", async function () {
      await contract.logAccessEvent(
        sampleHash, "user_ok", "SELECT", "public.products", 40, ""
      );
      expect(await contract.getAlertCount()).to.equal(0);
    });

    it("should emit both AccessEventLogged and ThreatAlertCreated", async function () {
      const tx = contract.logAccessEvent(
        sampleHash, "user_bad", "DELETE", "prod.ssn_data", 90, "QmX"
      );
      await expect(tx).to.emit(contract, "AccessEventLogged");
      await expect(tx).to.emit(contract, "ThreatAlertCreated");
    });
  });

  // ─────────────────── Manual Alert Creation ──────────────────────────────

  describe("createThreatAlert (manual)", function () {
    beforeEach(async function () {
      // Log a low-score event first (no auto-alert)
      await contract.logAccessEvent(
        sampleHash, "user_1", "SELECT", "prod.users", 30, ""
      );
    });

    it("should create a manual alert for an existing event", async function () {
      await contract.createThreatAlert(sampleHash, "HIGH");
      expect(await contract.getAlertCount()).to.equal(1);

      const alert = await contract.getThreatAlert(1);
      expect(alert.threatLevel).to.equal("HIGH");
      expect(alert.resolved).to.equal(false);
    });

    it("should reject alert for non-existent event", async function () {
      await expect(
        contract.createThreatAlert(sampleHash2, "LOW")
      ).to.be.revertedWith("DataShieldAudit: event does not exist");
    });

    it("should reject empty threat level", async function () {
      await expect(
        contract.createThreatAlert(sampleHash, "")
      ).to.be.revertedWith("DataShieldAudit: threat level cannot be empty");
    });

    it("should emit ThreatAlertCreated", async function () {
      await expect(contract.createThreatAlert(sampleHash, "CRITICAL"))
        .to.emit(contract, "ThreatAlertCreated")
        .withArgs(1, sampleHash, "CRITICAL", (ts) => ts > 0n);
    });
  });

  // ─────────────────── Alert Resolution ───────────────────────────────────

  describe("resolveAlert", function () {
    beforeEach(async function () {
      await contract.logAccessEvent(
        sampleHash, "user_bad", "DELETE", "prod.ssn_data", 85, ""
      );
      // Alert #1 auto-created
    });

    it("should mark an alert as resolved", async function () {
      await contract.resolveAlert(1);
      const alert = await contract.getThreatAlert(1);
      expect(alert.resolved).to.equal(true);
      expect(alert.responderAddress).to.equal(owner.address);
    });

    it("should allow any address to resolve an alert", async function () {
      await contract.connect(addr1).resolveAlert(1);
      const alert = await contract.getThreatAlert(1);
      expect(alert.resolved).to.equal(true);
      expect(alert.responderAddress).to.equal(addr1.address);
    });

    it("should reject resolving a non-existent alert", async function () {
      await expect(contract.resolveAlert(999)).to.be.revertedWith(
        "DataShieldAudit: alert does not exist"
      );
    });

    it("should reject resolving an already-resolved alert", async function () {
      await contract.resolveAlert(1);
      await expect(contract.resolveAlert(1)).to.be.revertedWith(
        "DataShieldAudit: alert already resolved"
      );
    });

    it("should emit ThreatAlertResolved", async function () {
      await expect(contract.resolveAlert(1))
        .to.emit(contract, "ThreatAlertResolved")
        .withArgs(1, owner.address, (ts) => ts > 0n);
    });
  });

  // ─────────────────── Threshold Management ──────────────────────────────

  describe("updateThreshold", function () {
    it("should allow the owner to update the threshold", async function () {
      await contract.updateThreshold(50);
      expect(await contract.alertThreshold()).to.equal(50);
    });

    it("should reject non-owner attempts", async function () {
      await expect(
        contract.connect(addr1).updateThreshold(50)
      ).to.be.revertedWith("DataShieldAudit: caller is not the owner");
    });

    it("should reject threshold above 100", async function () {
      await expect(contract.updateThreshold(101)).to.be.revertedWith(
        "DataShieldAudit: threshold must be 0-100"
      );
    });

    it("should emit ThresholdUpdated with old and new values", async function () {
      await expect(contract.updateThreshold(50))
        .to.emit(contract, "ThresholdUpdated")
        .withArgs(70, 50);
    });
  });

  // ─────────────────── Getter Functions ───────────────────────────────────

  describe("Getter functions", function () {
    beforeEach(async function () {
      // Event 1: low score — no alert
      await contract.logAccessEvent(
        sampleHash, "user_1", "SELECT", "prod.users", 30, ""
      );
      // Event 2: high score — auto-alert (#1)
      await contract.logAccessEvent(
        sampleHash2, "user_2", "DELETE", "prod.payments", 85, "Qm1"
      );
      // Event 3: critical score — auto-alert (#2)
      await contract.logAccessEvent(
        sampleHash3, "user_3", "DROP", "prod.ssn_data", 95, "Qm2"
      );
    });

    it("getEventCount returns correct count", async function () {
      expect(await contract.getEventCount()).to.equal(3);
    });

    it("getAlertCount returns correct count", async function () {
      expect(await contract.getAlertCount()).to.equal(2);
    });

    it("getAllEventHashes returns all hashes", async function () {
      const hashes = await contract.getAllEventHashes();
      expect(hashes.length).to.equal(3);
      expect(hashes[0]).to.equal(sampleHash);
      expect(hashes[1]).to.equal(sampleHash2);
      expect(hashes[2]).to.equal(sampleHash3);
    });

    it("getAllAlertIds returns all IDs", async function () {
      const ids = await contract.getAllAlertIds();
      expect(ids.length).to.equal(2);
      expect(ids[0]).to.equal(1);
      expect(ids[1]).to.equal(2);
    });

    it("getUnresolvedAlerts returns only unresolved", async function () {
      // Resolve alert #1
      await contract.resolveAlert(1);

      const unresolved = await contract.getUnresolvedAlerts();
      expect(unresolved.length).to.equal(1);
      expect(unresolved[0].alertId).to.equal(2);
      expect(unresolved[0].resolved).to.equal(false);
    });

    it("getUnresolvedAlerts returns empty when all resolved", async function () {
      await contract.resolveAlert(1);
      await contract.resolveAlert(2);

      const unresolved = await contract.getUnresolvedAlerts();
      expect(unresolved.length).to.equal(0);
    });
  });
});
