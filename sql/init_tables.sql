
CREATE TABLE IF NOT EXISTS administrator(
	idAdministrator INT NOT NULL AUTO_INCREMENT,
	username VARCHAR(32) NOT NULL,
    PRIMARY KEY (idAdministrator)
);

CREATE TABLE IF NOT EXISTS subject(
	idSubject INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    creatorID INT,
    PRIMARY KEY (idSubject),
    FOREIGN KEY (creatorID) REFERENCES administrator(idAdministrator)
);

CREATE TABLE IF NOT EXISTS class(
	idClass INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    lessons INT,
    creatorID INT NOT NULL,
    lastlearningweekday	INT DEFAULT 4,
    PRIMARY KEY (idClass),
    UNIQUE (name),
    FOREIGN KEY (creatorID) REFERENCES administrator(idAdministrator)
);

CREATE TABLE IF NOT EXISTS classsubject(
	idClasssubject INT NOT NULL AUTO_INCREMENT,
    classID INT NOT NULL,
    subjectID INT NOT NULL,
    PRIMARY KEY (idClasssubject),
    FOREIGN KEY (classID) REFERENCES class(idClass),
    FOREIGN KEY (subjectID) REFERENCES subject(idSubject)
);

CREATE TABLE IF NOT EXISTS classadministrator(
	idClassadministrator INT NOT NULL AUTO_INCREMENT,
    classID INT NOT NULL,
    administratorID INT NOT NULL,
    PRIMARY KEY (idClassadministrator),
    FOREIGN KEY (classID) REFERENCES class(idClass),
    FOREIGN KEY (administratorID) REFERENCES administrator(idAdministrator)
);

CREATE TABLE IF NOT EXISTS lesson(
	idLesson INT NOT NULL AUTO_INCREMENT,
    classID INT NOT NULL,
    subjectID INT NOT NULL,
    weekday INT NOT NULL,
    position INT NOT NULL,
    PRIMARY KEY (idLesson),
    FOREIGN KEY (classID) REFERENCES class(idClass),
    FOREIGN KEY (subjectID) REFERENCES subject(idSubject)
);

