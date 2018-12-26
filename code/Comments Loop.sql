#Campaign Comments

DESC rl_op.CampaignComments;

DROP TABLE IF EXISTS builder.Keri_Comments_MCID;
CREATE TABLE builder.Keri_Comments_MCID
SELECT DISTINCT idCampaign_Master	
FROM rl_report.CSR_Summary CSR
LEFT JOIN rl_finance.RLExcludeBusiness RL 
	ON CSR.idBusiness = RL.idBusiness
WHERE RL.idBusiness IS NULL
	#AND idOffer = 1
	AND csr_year >= 2009
	AND net_cost > 0
;


DROP TABLE IF EXISTS temp.Keri_Comments;
CREATE TABLE temp.Keri_Comments (
CC_Year INT(4),
CC_Month TINYINT,
MCID INT(10) UNSIGNED,
CID INT(10) UNSIGNED,
Campaign_Name VARCHAR(255),
MAID INT(10) UNSIGNED,
BusinessUser SMALLINT,
System SMALLINT,
Stop_Request SMALLINT,
idOffer INT(10) UNSIGNED,
PRIMARY KEY (CC_Year, CC_Month, CID))
;


DROP PROCEDURE IF EXISTS builder.Keri_Comments_Loop;
DELIMITER $$

CREATE PROCEDURE builder.Keri_Comments_Loop()
BEGIN

SET	@MCID	:=	(SELECT MIN(idCampaign_Master) FROM builder.Keri_Comments_MCID);

WHILE @MCID IS NOT NULL DO

INSERT INTO temp.Keri_Comments
SELECT YEAR(CC.cc_entered) AS CC_Year,
	MONTH(CC.cc_entered) AS CC_Month,
	C.Campaign_idCampaign_Master_FK AS MCID,
    Campaign_idCampaign_FK AS CID,
    campaign_name,
    Advertiser_idAdvertiser_Master_FK AS MAID,
	SUM(IF(BusinessUser_idBusinessUser_FK <> 1,1,0)) AS BusinessUser,
    SUM(IF(BusinessUser_idBusinessUser_FK = 1,1,0)) AS System,
    MAX(IF(cc_coment LIKE '*USER STOP REQUEST*%',1,0)) AS Stop_Request,
    Offer_idOffer_FK AS idOffer
FROM rl_op.CampaignComments CC
JOIN rl_op.Campaign C 
	ON CC.Campaign_idCampaign_FK = C.idCampaign
JOIN rl_op.Advertiser A 
	ON C.Advertiser_idAdvertiser_FK = A.idAdvertiser
WHERE Campaign_idCampaign_Master_FK = @MCID
	AND cc_entered BETWEEN '2009-01-01' AND '2018-03-31'
GROUP BY 1,2,CC.Campaign_idCampaign_FK
;

DELETE FROM builder.Keri_Comments_MCID WHERE idCampaign_Master = @MCID;
SET	@MCID	:=	(SELECT MIN(idCampaign_Master) FROM builder.Keri_Comments_MCID);

END WHILE;
END $$
DELIMITER ;

CALL builder.Keri_Comments_Loop;


desc temp.Keri_Comments;
desc rl_report.CSR_Summary;
desc rl_analysis.BSC_Standards;
desc rl_reportview.MasterCampaignReport;
desc rl_analysis.Net_New_Budget_V3;

SELECT * FROM temp.Keri_Comments WHERE idOffer <> 1 LIMIT 1000;


DROP TABLE IF EXISTS temp.Keri_Churn_Model;

DROP PROCEDURE IF EXISTS builder.Keri_Churn_Loop;
DELIMITER $$

CREATE PROCEDURE builder.Keri_Churn_Loop()
BEGIN

SET @MCID := (SELECT MIN(idCampaign_Master) FROM builder.Keri_Comments_MCID);

WHILE @MCID IS NOT NULL DO

	
INSERT INTO temp.Keri_Churn_Model
SELECT 
	csr_year,
    csr_month,
    CSR.idCampaign_Master,
    CSR.idCampaign,
	CSR.idAdvertiser,
	A.advertiser_name,
	advertiser_city,
	advertiser_state,
	advertiser_zipcode,
	idBusinessCategory,
    business_category, 
	idBusinessSubCategory,
    bsc_name as business_subcategory,
    CSR.idOffer,
    Product,
	stop_request,
	change_type AS Adv_Change_Type,
    CSR.campaign_budget,
    IF(net_cost+net_cost_adjustment < 0,0,net_cost+net_cost_adjustment) AS Spend,
    CSR.clicks,
    CSR.impressions,
    CSR.calls,
    CSR.qualified_calls,
    CSR.emails,
    CSR.cvt,
    CSR.qualified_web_events,
    CC.BusinessUser,
    CC.System
   
FROM rl_report.CSR_Summary CSR
JOIN rl_reportview.MasterCampaignReport MCR
	ON CSR.idCampaign = MCR.idCampaign
JOIN rl_op.Advertiser A 
	ON CSR.idAdvertiser = A.idAdvertiser
JOIN rl_analysis.Net_New_Budget_V3 NNB
	ON CSR.idAdvertiser_Master = NNB.first_aid
    AND CSR.csr_year = YEAR(NNB.reporting_date)
    AND CSR.csr_month = MONTH(NNB.reporting_date)
JOIN rl_analysis.OfferKey O 
	ON CSR.idOffer = O.idOffer 
LEFT JOIN temp.Keri_Comments CC
	ON CSR.csr_year = CC.CC_Year
    AND CSR.csr_month = CC.CC_Month
    AND CSR.idCampaign = CC.CID
WHERE CSR.idCampaign_Master = @MCID
	AND csr_year >= 2009
GROUP BY csr_year, csr_month, CSR.idCampaign
;

DELETE FROM builder.Keri_Comments_MCID WHERE @MCID = idCampaign_Master; 
SET @MCID :=	(SELECT MIN(idCampaign_Master) FROM builder.Keri_Comments_MCID);

END WHILE;
END $$

DELIMITER ;

CALL builder.Keri_Churn_Loop;

ALTER TABLE temp.Keri_Churn_Model ADD INDEX (csr_year, csr_month, idCampaign);
ALTER TABLE temp.Keri_Churn_Model ADD PRIMARY KEY (csr_year, csr_month, idCampaign);
ALTER TABLE temp.Keri_Churn_Model ADD COLUMN AdvTrans INT(1);

SELECT SUM(IF(AdvTrans = 1,1,0)) AS Transfers,
	SUM(IF(AdvTrans = 0,1,0)) AS Not_Transfers
FROM temp.Keri_Churn_Model;

SELECT * FROM temp.Keri_Churn_Model LIMIT 1000;

DESC temp.Keri_Churn_Model;


DROP TABLE IF EXISTS builder.Keri_AdvTrans_Copy;

CREATE TABLE builder.Keri_AdvTrans_Copy
SELECT YEAR(created) AS adv_year,
				MONTH(created) AS adv_month,
				Campaign_idCampaign_FK AS idCampaign,
                1 AS AdvTrans
			FROM rl_op.AdvertiserTransferCampaignLog ADV
            WHERE YEAR(created) >= 2009 
            GROUP BY adv_year,adv_month,Campaign_idCampaign_FK
;
DESC builder.Keri_AdvTrans_Copy;

ALTER TABLE builder.Keri_AdvTrans_Copy ADD INDEX (adv_year,adv_month,idCampaign);
ALTER TABLE builder.Keri_AdvTrans_Copy ADD PRIMARY KEY (adv_year,adv_month,idCampaign);


UPDATE temp.Keri_Churn_Model CM
SET CM.AdvTrans = 1
WHERE EXISTS (
	SELECT 1 FROM builder.Keri_AdvTrans_Copy TC
	WHERE CM.csr_year = TC.adv_year
		AND CM.csr_month = TC.adv_month
		AND CM.idCampaign = TC.idCampaign
		)
;

UPDATE temp.Keri_Churn_Model CM
SET CM.AdvTrans = 0
WHERE NOT EXISTS (
	SELECT 1 FROM builder.Keri_AdvTrans_Copy TC
	WHERE CM.csr_year = TC.adv_year
		AND CM.csr_month = TC.adv_month
		AND CM.idCampaign = TC.idCampaign
		)

