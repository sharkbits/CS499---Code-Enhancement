
#include<iostream>
#include<string>

using namespace std;


class Clock
{
private:
    unsigned int hours;
    unsigned int minutes;
    unsigned int seconds;
    string AM_or_PM = "";

public:
    Clock(unsigned int hours, unsigned int minutes, unsigned int seconds)
    {
        if(hours < 24 && minutes < 60 && seconds < 60){
            this->hours = hours;
            this->minutes = minutes;
            this->seconds = seconds;
        }else{
            throw invalid_argument("Invalid initial values");
        }
    }

    void addHour(){
        if(this->hours == 23){
            this->hours=0;
            return;
        }
        this->hours++;
    }
    void addMinute()
    {
        if(this->minutes == 59){
            this->minutes = 0;
            this->hours++;
            return;
        }
        this->minutes++;
    }
    void addSecond()
    {
        if(this->seconds == 59){
            this->seconds = 0;
            this->minutes++;
            return;
        }
        this->seconds++;
    }

    string format12HRTime()
    {
        unsigned int hours_AM_PM = this->hours % 12 != 0 ? this->hours % 12 : 12;

        if (this->hours > 11)
            this->AM_or_PM = "PM";
        else
        {
            this->AM_or_PM = "AM";
        }
        return to_string(hours_AM_PM) + ":" + to_string(this->minutes) + ":" + to_string(this->seconds) + this->AM_or_PM;
    }

    void displayMenu(){

        cout << "    12hr time" << "    *     24hr time" << endl;
        cout << "* " << this->format12HRTime() << "   *    " << this->format24HRTime() << endl; 

        cout << "Main Menu" << endl;
        cout << "***************************" << endl;
        cout << "1. Add 1 Hour" << endl;
        cout << "2. Add 1 Minute" << endl;
        cout << "3. Add 1 Second" << endl;
        cout << "4. Exit Program" << endl;
        cout << "***************************" << endl;
    }

    string format24HRTime()
    {
        return to_string(this->hours) + ":" + to_string(this->minutes) + ":" + to_string(this->seconds);
    }
};

int main(){
    try{

        Clock c = Clock(11, 30, 50);

        int choice;
        string userInput;

        while (true)
        {

            c.displayMenu();
            cin >> userInput;
            choice = stoi(userInput);

            if (choice == 4) break;

            if (choice == 1)
                c.addHour();
            else if (choice == 2)
                c.addMinute();
            else if (choice == 3)
                c.addSecond();
            else{
                cout << "invalid response please try again..." << endl;
            }
        }

    }
    catch (const std::invalid_argument &e)
    {
        cout << e.what();
    }

    cout << "Program exit successfully!" << endl;

    return 0;
}